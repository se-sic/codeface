# This file is part of Codeface. Codeface is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Copyright 2010, 2011 by Wolfgang Mauerer <wm@linux-kernel.net>
# Copyright 2012, 2013 by Siemens AG, Wolfgang Mauerer <wolfgang.mauerer@siemens.com>
# All Rights Reserved.

import re
from email.Utils import parseaddr
from PersonInfo import PersonInfo
from logging import getLogger; log = getLogger(__name__)
import httplib
import urllib
import json
import string
import random
import time
from ..util import encode_as_utf8

class idManager:
    """Provide unique IDs for developers.

    This class provides an interface to the REST id server. Heuristics to
    detect developers who operate under multiple identities are included
    in the server."""

    def __init__(self, dbm, conf):
        self.subsys_names = []

        # Map IDs to an instance of PersonInfo
        self.persons = {}

        # Map a name, email address, or a combination of both to the numeric ID
        # assigned to the developer
        self.person_ids = {}

        # Cache identical requests to the server
        self._cache = {}

        self.fixup_emailPattern = re.compile(r'([^<]+)\s+<([^>]+)>')
        self.commaNamePattern = re.compile(r'([^,\s]+),\s+(.+)')

        self._idMgrServer = conf["idServiceHostname"]
        self._idMgrPort = conf["idServicePort"]
        self._conn = httplib.HTTPConnection(self._idMgrServer, self._idMgrPort)

        # Create a project ID
        self._dbm = dbm
        # TODO: Pass the analysis method to idManager via the configuration
        # file. However, the method should not influence the id scheme so
        # that the results are easily comparable.
        self._projectID = self._dbm.getProjectID(conf["project"],
                                                 conf["tagging"])

        # Construct request headers
        self.headers = {"Content-type":
                            "application/x-www-form-urlencoded; charset=utf-8",
                        "Accept": "text/plain"}

    # We need the subsystem names because PersonInfo instances
    # are created from this class -- and we want to know in which
    # subsystem(s) a developer is active
    def setSubsysNames(self, subsys_names):
        self.subsys_names = subsys_names

    def getSubsysNames(self):
        return self.subsys_names

    def _decompose_addr(self, addr):
        addr = addr.replace("[", "").replace("]", "")
        (name, email) = parseaddr(addr)

        # Handle cases where the name is unknown from commits that potentially
        # predate the era of git, where only an e-mail address was given.
        # In such a case, we set the name to the e-mail address. Otherwise,
        # all authors with unknown name would be matched to one person.
        if (name == "unknown" or name == "unknown (none)" or name == "none"):
            name = email

        # The eMail parser cannot handle Surname, Name <email@domain.tld> properly.
        # Provide a fixup hack for this case
        if (name == "" or email.count("@") == 0):
            m = re.search(self.fixup_emailPattern, addr)
            if m:
                name = m.group(1)
                email = m.group(2)
                m2 = re.search(self.commaNamePattern, name)
                if m2:
                    # Replace "Surname, Name" by "Name Surname"
                    name = "{0} {1}".format(m2.group(2), m2.group(1))

                # print "Fixup for addr {0} required -> ({1}/{2})".format(addr, name, email)
            else:
                # check for the following special format: email@domain.tld <>
                strangePattern = re.compile(r'(.*@.*)\s+(<>)')
                m3 = re.search(strangePattern, addr)
                if m3:
                    # Replace addr by "email <email@domain.tld>"
                    name = m3.group(1).split("@")[0] # get name before @ symbol
                    email = m3.group(1)
                    # print "Fixup for addr {0} required -> ({1}/{2})".format(addr, name, email)
                else:
                    # In this case, no eMail address was specified.
                    # print("Fixup for email required, but FAILED for {0}".format(addr))
                    name = addr
                    rand_str = "".join(random.choice(string.ascii_lowercase + string.digits)
                                       for i in range(10))
                    email = "could.not.resolve@" + rand_str

        email = email.lower()

        name = self._cleanName(name)
        email = self._cleanName(email)

        return (name, email)

    def _query_user_id(self, name, email):
        """Query the ID database for a contributor ID"""

        name = encode_as_utf8(name)
        params = urllib.urlencode({'projectID': self._projectID,
                                   'name': name,
                                   'email': email})

        try:
            self._conn.request("POST", "/post_user_id", params, self.headers)
            res = self._conn.getresponse()
        except:
            retryCount = 0
            successful = False
            while (retryCount <= 10 and not successful):
                log.warning("Could not reach ID service. Try to reconnect " \
                            "(attempt {}).".format(retryCount));
                self._conn.close()
                self._conn = httplib.HTTPConnection(self._idMgrServer, self._idMgrPort)
                time.sleep(60)
                #self._conn.ping(True)
                try:
                    self._conn.request("POST", "/post_user_id", params, self.headers)
                    res = self._conn.getresponse()
                    successful = True
                except:
                    if retryCount < 10:
                        retryCount += 1
                    else:
                        retryCount += 1
                        log.exception("Could not reach ID service. Is the server running?\n")
                        raise

        # TODO: We should handle errors by throwing an exception instead
        # of silently ignoring them
        result = res.read()
        jsond = json.loads(result)
        try:
            id = jsond["id"]
        except KeyError:
            raise Exception("Bad response from server: '{}'".format(jsond))

        return (id)

    def getPersonID(self, addr):
        """Obtain a unique ID from contributor identity credentials.

        The IDs are managed by a central database accessed via REST.
        Managing multiple identities for the same person is also
        handled there. Safety against concurrent access is provided by
        the database.
        """

        (name, email) = self._decompose_addr(addr)
        if not (name, email) in self._cache:
            self._cache[(name, email)] = self._query_user_id(name, email)
        ID = self._cache[(name, email)]

        # Construct a local instance of PersonInfo for the contributor
        # if it is not yet available
        if not self.persons.has_key(ID):
            self.persons[ID] = PersonInfo(self.subsys_names, ID, name, email)

        return ID

    def getPersonFromDB(self, person_id):
        """Query the ID database for a contributor and all corresponding data"""

        try:
            self._conn.request("GET", "/getUser/{}".format(person_id), headers=self.headers)
            res = self._conn.getresponse()
        except:
            self._conn.close()
            self._conn = httplib.HTTPConnection(self._idMgrServer, self._idMgrPort)
            retryCount = 0
            successful = False
            while (retryCount <= 10 and not successful):
                log.warning("Could not reach ID service. Try to reconnect " \
                            "(attempt {}).".format(retryCount));
                self._conn.close()
                self._conn = httplib.HTTPConnection(self._idMgrServer, self._idMgrPort)
                time.sleep(60)
                #self._conn.ping(True)
                try:
                    self._conn.request("GET", "/getUser/{}".format(person_id), headers=self.headers)
                    res = self._conn.getresponse()
                    successful = True
                except:
                    if retryCount < 10:
                        retryCount += 1
                    else:
                        retryCount += 1
                        log.exception("Could not reach ID service. Is the server running?\n")
                        raise

        result = res.read()
        jsond = json.loads(result)[0]

        return (jsond)

    def getPersons(self):
        return self.persons

    def getPI(self, ID):
        return self.persons[ID]

    def _cleanName(self, name):
        # Remove or replace characters in names that are known
        # to cause parsing problems in later stages
        name = name.replace('\"', "")
        name = name.replace("\'", "")
        name = string.lstrip(string.rstrip(name))

        return name
