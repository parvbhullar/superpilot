from typing import Any
from typing import Type

from sqlalchemy.orm import Session

from super_store.connectors.models import InputType

from super_store.connectors.interfaces import BaseConnector
from super_store.connectors.interfaces import EventConnector
from super_store.connectors.interfaces import LoadConnector
from super_store.connectors.interfaces import PollConnector

from super_store.configs.constants import DocumentSource
from super_store.connectors.web.connector import WebConnector
from super_store.connectors.file.connector import LocalFileConnector

### Enable these connectors when needed
# from super_store.connectors.axero.connector import AxeroConnector
# from super_store.connectors.bookstack.connector import BookstackConnector
# from super_store.connectors.clickup.connector import ClickupConnector
# from super_store.connectors.confluence.connector import ConfluenceConnector
# from super_store.connectors.danswer_jira.connector import JiraConnector
# from super_store.connectors.discourse.connector import DiscourseConnector
# from super_store.connectors.document360.connector import Document360Connector
# from super_store.connectors.dropbox.connector import DropboxConnector
# from super_store.connectors.github.connector import GithubConnector
# from super_store.connectors.gitlab.connector import GitlabConnector
# from super_store.connectors.gmail.connector import GmailConnector
# from super_store.connectors.gong.connector import GongConnector
# from super_store.connectors.google_drive.connector import GoogleDriveConnector
# from super_store.connectors.google_site.connector import GoogleSitesConnector
# from super_store.connectors.guru.connector import GuruConnector
# from super_store.connectors.hubspot.connector import HubSpotConnector
# from super_store.connectors.linear.connector import LinearConnector
# from super_store.connectors.loopio.connector import LoopioConnector
# from super_store.connectors.mediawiki.wiki import MediaWikiConnector
# from super_store.connectors.notion.connector import NotionConnector
# from super_store.connectors.productboard.connector import ProductboardConnector
# from super_store.connectors.requesttracker.connector import RequestTrackerConnector
# from super_store.connectors.salesforce.connector import SalesforceConnector
# from super_store.connectors.sharepoint.connector import SharepointConnector
# from super_store.connectors.slab.connector import SlabConnector
# from super_store.connectors.slack.connector import SlackPollConnector
# from super_store.connectors.slack.load_connector import SlackLoadConnector
# from super_store.connectors.teams.connector import TeamsConnector
# from super_store.connectors.wikipedia.connector import WikipediaConnector
# from super_store.connectors.zendesk.connector import ZendeskConnector
# from super_store.connectors.zulip.connector import ZulipConnector
from super_store.db.credentials import backend_update_credential_json
from super_store.db.models import Credential


class ConnectorMissingException(Exception):
    pass


def identify_connector_class(
    source: DocumentSource,
    input_type: InputType | None = None,
) -> Type[BaseConnector]:
    connector_map = {
        DocumentSource.WEB: WebConnector,
        DocumentSource.FILE: LocalFileConnector,
        # DocumentSource.SLACK: {
        #     InputType.LOAD_STATE: SlackLoadConnector,
        #     InputType.POLL: SlackPollConnector,
        # },
        # DocumentSource.GITHUB: GithubConnector,
        # DocumentSource.GMAIL: GmailConnector,
        # DocumentSource.GITLAB: GitlabConnector,
        # DocumentSource.GOOGLE_DRIVE: GoogleDriveConnector,
        # DocumentSource.BOOKSTACK: BookstackConnector,
        # DocumentSource.CONFLUENCE: ConfluenceConnector,
        # DocumentSource.JIRA: JiraConnector,
        # DocumentSource.PRODUCTBOARD: ProductboardConnector,
        # DocumentSource.SLAB: SlabConnector,
        # DocumentSource.NOTION: NotionConnector,
        # DocumentSource.ZULIP: ZulipConnector,
        # DocumentSource.REQUESTTRACKER: RequestTrackerConnector,
        # DocumentSource.GURU: GuruConnector,
        # DocumentSource.LINEAR: LinearConnector,
        # DocumentSource.HUBSPOT: HubSpotConnector,
        # DocumentSource.DOCUMENT360: Document360Connector,
        # DocumentSource.GONG: GongConnector,
        # DocumentSource.GOOGLE_SITES: GoogleSitesConnector,
        # DocumentSource.ZENDESK: ZendeskConnector,
        # DocumentSource.LOOPIO: LoopioConnector,
        # DocumentSource.DROPBOX: DropboxConnector,
        # DocumentSource.SHAREPOINT: SharepointConnector,
        # DocumentSource.TEAMS: TeamsConnector,
        # DocumentSource.SALESFORCE: SalesforceConnector,
        # DocumentSource.DISCOURSE: DiscourseConnector,
        # DocumentSource.AXERO: AxeroConnector,
        # DocumentSource.CLICKUP: ClickupConnector,
        # DocumentSource.MEDIAWIKI: MediaWikiConnector,
        # DocumentSource.WIKIPEDIA: WikipediaConnector,
    }
    connector_by_source = connector_map.get(source, {})

    if isinstance(connector_by_source, dict):
        if input_type is None:
            # If not specified, default to most exhaustive update
            connector = connector_by_source.get(InputType.LOAD_STATE)
        else:
            connector = connector_by_source.get(input_type)
    else:
        connector = connector_by_source
    if connector is None:
        raise ConnectorMissingException(f"Connector not found for source={source}")

    if any(
        [
            input_type == InputType.LOAD_STATE
            and not issubclass(connector, LoadConnector),
            input_type == InputType.POLL and not issubclass(connector, PollConnector),
            input_type == InputType.EVENT and not issubclass(connector, EventConnector),
        ]
    ):
        raise ConnectorMissingException(
            f"Connector for source={source} does not accept input_type={input_type}"
        )

    return connector


def instantiate_connector(
    source: DocumentSource,
    input_type: InputType,
    connector_specific_config: dict[str, Any],
    credential: Credential,
    db_session: Session,
) -> BaseConnector:
    connector_class = identify_connector_class(source, input_type)
    connector = connector_class(**connector_specific_config)
    new_credentials = connector.load_credentials(credential.credential_json)

    if new_credentials is not None:
        backend_update_credential_json(credential, new_credentials, db_session)

    return connector
