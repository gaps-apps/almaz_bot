from .handlers import router as start_router
from .menu import router as menu_router
from .payment import router as payment_router

__ALL__ = [start_router, menu_router, payment_router]
