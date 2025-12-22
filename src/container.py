"""Dependency injection container."""
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    """
    Application dependency injection container.

    Uses dependency-injector for managing service dependencies
    and lifecycle.
    """

    # Configuration
    config = providers.Configuration()

    # Database (will be added in Sprint 1)
    # db = providers.Singleton(...)

    # Redis Client (will be added in Sprint 1)
    # redis_client = providers.Singleton(
    #     RedisClient,
    #     url=config.redis.url
    # )

    # Repositories (will be added in Sprint 1)
    # user_repository = providers.Factory(
    #     UserRepository,
    #     session=db.provided.session
    # )

    # Services (will be added in Sprint 2+)
    # user_service = providers.Factory(
    #     UserService,
    #     user_repository=user_repository
    # )

    # Plugins (will be added in Sprint 4)
    # plugin_manager = providers.Singleton(PluginManager)
    # stripe_plugin = providers.Singleton(
    #     StripePlugin,
    #     api_key=config.stripe.api_key
    # )

    # Event Dispatcher (will be added in Sprint 4)
    # event_dispatcher = providers.Singleton(EventDispatcher)
