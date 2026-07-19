"""The primary SDK entry point.

`DriveThruRpgSdk` is the root object that holds SDK configuration and
manages the active authentication session. Start here when integrating the
DriveThruRPG API into your application.
"""

from __future__ import annotations

from dtrpg_sdk.auth.session import AuthSession, AuthSessionError, AuthTokenResponse
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import UnauthenticatedError, UnconfiguredError
from dtrpg_sdk.library.client import LibraryClient


class DriveThruRpgSdk:
    """The DriveThruRPG SDK client.

    `DriveThruRpgSdk` coordinates SDK-level configuration and authentication
    session lifecycle. It must be configured before any authenticated API
    calls can succeed.

    Lifecycle:
        1. Create an SDK instance, optionally supplying `Config` upfront.
        2. After a successful API login, call `apply_auth_response` to store
           the session.
        3. Use `require_session` to obtain the active session before making
           requests.
        4. Call `invalidate_session` when the API reports a session error,
           or `clear_session` to log out.

    Examples:
        >>> sdk = DriveThruRpgSdk.with_config(Config(application_key="my-app-key"))
        >>> response = AuthTokenResponse("jwt", "refresh", 9_999_999_999)
        >>> session = sdk.apply_auth_response(response)
        >>> session.token
        'jwt'
    """

    def __init__(self) -> None:
        """Creates an unconfigured SDK instance.

        Call `configure` before making any API calls, or prefer
        `with_config` if the configuration is available at construction
        time.
        """
        self._config: Config | None = None
        self._session: AuthSession | None = None

    @staticmethod
    def with_config(config: Config) -> DriveThruRpgSdk:
        """Creates an SDK instance pre-loaded with the given `Config`."""
        sdk = DriveThruRpgSdk()
        sdk._config = config
        return sdk

    def configure(self, config: Config) -> None:
        """Sets or replaces the SDK's configuration.

        This can be called at any time, including after the SDK has been
        used. Replacing the configuration does not automatically clear an
        existing session.
        """
        self._config = config

    @property
    def config(self) -> Config | None:
        """Returns the current configuration, or `None` if the SDK is unconfigured."""
        return self._config

    @property
    def session(self) -> AuthSession | None:
        """Returns the current authentication session, or `None` if unauthenticated."""
        return self._session

    def require_config(self) -> Config:
        """Returns the current configuration, or raises `UnconfiguredError` if absent.

        Use this in call chains where a missing config should surface as an
        error.
        """
        if self._config is None:
            raise UnconfiguredError()
        return self._config

    def require_session(self) -> AuthSession:
        """Returns the current session, or raises `UnauthenticatedError` if absent.

        Use this in call chains where a missing session should surface as an
        error.
        """
        if self._session is None:
            raise UnauthenticatedError()
        return self._session

    def apply_auth_response(self, response: AuthTokenResponse) -> AuthSession:
        """Stores a new authentication session derived from a raw API token response.

        Raises:
            UnconfiguredError: If the SDK has not been configured yet.

        Returns the newly stored session on success.
        """
        self.require_config()
        self._session = AuthSession.from_api_response(response)
        return self.require_session()

    def clear_session(self) -> None:
        """Removes the current authentication session without recording an error.

        Use this for voluntary log-out flows. For API-reported session
        failures, prefer `invalidate_session`.
        """
        self._session = None

    def invalidate_session(self, error: AuthSessionError) -> AuthSessionError:
        """Removes the current session and records the error that caused it.

        Raises:
            UnauthenticatedError: If there is no session to invalidate.

        Returns the provided `error` so callers can inspect or propagate it.
        """
        self.require_session()
        self.clear_session()
        return error

    def library_client(self) -> LibraryClient:
        """Creates a `LibraryClient` from the current configuration and session.

        Raises:
            UnconfiguredError: If the SDK has not been configured.
            UnauthenticatedError: If there is no active session.
        """
        config = self.require_config()
        token = self.require_session().token
        return LibraryClient(config, token)
