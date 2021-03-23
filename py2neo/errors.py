#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright 2011-2021, Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class Neo4jError(Exception):
    """ Base exception class for modelling error status codes returned
    by Neo4j.

    For details of the status codes available, visit:
    https://neo4j.com/docs/status-codes/current/

    """

    @classmethod
    def hydrate(cls, data):
        code = data.get("code")
        message = data.get("message")
        return cls(message, code)

    @classmethod
    def split_code(cls, code):
        """ Splits a status code, returning a 3-tuple of
        classification, category and title.
        """
        try:
            parts = code.split(".")
        except AttributeError:
            raise ValueError(code)
        else:
            if len(parts) == 4 and parts[0] == "Neo":
                return parts[1], parts[2], parts[3]
            else:
                raise ValueError(code)

    def __new__(cls, message, code):
        classification, _, _ = cls.split_code(code)
        if classification == "ClientError":
            return Exception.__new__(ClientError)
        elif classification == "DatabaseError":
            return Exception.__new__(DatabaseError)
        elif classification == "TransientError":
            return Exception.__new__(TransientError)
        else:
            return Exception.__new__(cls)

    def __init__(self, message, code):
        super(Neo4jError, self).__init__(message)
        self.__code = code
        self.__classification, self.__category, self.__title = self.split_code(self.__code)

    def __str__(self):
        return "[%s.%s] %s" % (self.category, self.title, super(Neo4jError, self).__str__())

    @property
    def code(self):
        return self.__code

    @property
    def classification(self):
        return self.__classification

    @property
    def category(self):
        return self.__category

    @property
    def title(self):
        return self.__title

    @property
    def message(self):
        return self.args[0]

    def should_retry(self):
        return False

    def should_invalidate_routing_table(self):
        return False


class ClientError(Neo4jError):

    def should_invalidate_routing_table(self):
        return self.category == "Cluster" and self.title == "NotALeader"

    def should_retry(self):
        return self.category == "Cluster" and self.title == "NotALeader"


class DatabaseError(Neo4jError):
    pass


class TransientError(Neo4jError):

    def should_retry(self):
        if self.category == "Transaction":
            return self.title not in ("Terminated", "LockClientStopped")
        else:
            return True
