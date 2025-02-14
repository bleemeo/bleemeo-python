# Copyright 2015-2025 Bleemeo
#
# bleemeo.com an infrastructure monitoring solution in the Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class AgentType:
    AWS_ACCOUNT = "aws_account"
    AWS_TRUSTED_ADVISOR = "aws_trusted_advisor"
    AWS_DYNAMODB = "aws_dynamodb"
    AWS_EC2 = "aws_ec2"
    AWS_ELB = "aws_elb"
    AWS_RDS = "aws_rds"
    AWS_S3 = "aws_s3"
    AGENT = "agent"
    MONITOR = "connection_check"
    SNMP = "snmp"
    K8S = "kubernetes"
    VSPHERE_CLUSTER = "vsphere_cluster"
    VSPHERE_HOST = "vsphere_host"
    VSPHERE_VM = "vsphere_vm"
    APPLICATION_TYPE = "application"


class DisconnectionReason:
    CLEAN_SHUTDOWN = 1
    AGENT_TIMEOUT = 2
    AGENT_AUTO_UPGRADE = 3
    AGENT_UPGRADE = 4


class GloutonDiagnostics:
    CRASH = 0
    ON_DEMAND = 1


class Graph:
    LINE = 0
    STACK = 1
    PIE = 2
    GAUGE = 3
    AVAILABILITY_TIMELINE = 4
    NUMBER = 5
    STATUS = 6
    SNMP_STATUS = 7
    TEXT = 8
    IMAGE = 9
    HEATMAP_STATUS = 10
    BAR = 11


class ReportPeriod:
    WEEKLY = 0
    MONTHLY = 1


class ReportIncluded:
    NONE = 0
    PARTIAL = 1
    FULL = 2


class ConfigItemSource:
    UNKNOWN = 0
    DEFAULT = 1
    FILE = 2
    ENV = 3
    API = 4


class ConfigItemType:
    ANY = 0
    INT = 1
    FLOAT = 2
    BOOL = 3
    STRING = 4
    LIST_STR = 10
    LIST_INT = 11
    MAP_STR_STR = 20
    MAP_STR_INT = 21
    THRESHOLDS = 30
    SERVICES = 31
    NAME_INSTANCES = 32
    BLACKBOX_TARGETS = 33
    PROMETHEUS_TARGETS = 34
    TYPE_SNMP_TARGETS = 35
    TYPE_LOG_INPUTS = 36


class Status:
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class TagType:
    AUTOMATIC_API = 0
    CREATED_BY_GLOUTON = 1
    CREATED_BY_FRONTEND = 2
    AUTOMATIC_GLOUTON = 3
    AUTOMATIC_API_SERVICE = 4
    NO_TYPE = 10
