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

from enum import Enum


class Resource(Enum):
    """A Resource represents a route to a model on the Bleemeo API."""

    ACCOUNT = "v1/account/"
    ACCOUNT_CONFIG = "v1/accountconfig/"
    AGENT = "v1/agent/"
    AGENT_CONFIG = "v1/agentconfig/"
    AGENT_FACT = "v1/agentfact/"
    AGENT_TYPE = "v1/agenttype/"
    APPLICATION = "v1/application/"
    AUDITLOG = "v1/auditlog/"
    AWS_INTEGRATION = "v1/awsintegration/"
    CONTACTS_GROUP = "v1/contactsgroup/"
    CONTAINER = "v1/container/"
    DASHBOARD = "v1/dashboard/"
    EVENT = "v1/event/"
    FLAPPY_CONFIGURATION = "v1/flappyconfiguration/"
    FORECAST = "v1/forecast/"
    FORECAST_CONFIGURATION = "v1/forecastconfiguration/"
    GLOUTON_CONFIG_ITEM = "v1/gloutonconfigitem/"
    GLOUTON_CRASH_REPORT = "v1/gloutoncrashreport/"
    GLOUTON_DIAGNOSTIC = "v1/gloutondiagnostic/"
    HEALTHCHECK = "v1/healthcheck/"
    INTEGRATION = "v1/integration/"
    INTEGRATION_TEMPLATE = "v1/integrationtemplate/"
    DASHBOARD_LAYOUT = "v1/dashboardlayout/"
    LIMIT = "v1/limit/"
    METRIC = "v1/metric/"
    METRIC_ANNOTATION = "v1/metricannotation/"
    METRIC_NAME = "v1/metricname/"
    METRIC_OPERATION = "v1/metricoperation/"
    METRIC_TEMPLATE_GROUP = "v1/metrictemplategroup/"
    NOTIFICATION_EXECUTION = "v1/notificationexecution/"
    NOTIFICATION_RULE = "v1/notificationrule/"
    PUBLIC_STATUS_PAGE = "v1/publicstatuspage/"
    RECORDING_RULE = "v1/recordingrule/"
    REPORT = "v1/report/"
    SERVER_GROUP = "v1/servergroup/"
    SERVICE = "v1/service/"
    SESSION = "v1/session/"
    SILENCE = "v1/silence/"
    SILENCE_RECURRENT = "v1/silencerecurrent/"
    SLO = "v1/slo/"
    TAG = "v1/tag/"
    USER = "v1/user/"
    WIDGET = "v1/widget/"
    WIDGET_ANNOTATION = "v1/widgetannotation/"

    def __str__(self) -> str:
        return self.value
