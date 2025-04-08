# Import all views to make them available when importing from store.views

# First import from the modular view files in the views package
from .views import *
from .delivery_views import *
from .auth_views import *

# To avoid circular imports, we'll directly import the main views.py file
# and make its functions available in this namespace

# Import the main views module directly
import sys
import importlib.util

# We need to directly access the main views.py file without causing circular imports
# This is done by importing the module directly from its file path

# Get the path to the main views.py file
import os
parent_dir = os.path.dirname(os.path.dirname(__file__))
main_views_path = os.path.join(parent_dir, 'views.py')

# Import the main views module using spec to avoid circular imports
spec = importlib.util.spec_from_file_location('store.main_views', main_views_path)
main_views = importlib.util.module_from_spec(spec)
sys.modules['store.main_views'] = main_views
spec.loader.exec_module(main_views)

# Now we can import all the view functions from the main views module
# and make them available in this namespace

# Get all the functions from the main views module
for name in dir(main_views):
    # Skip private attributes and modules
    if not name.startswith('_') and not name in globals():
        # Get the attribute from the main views module
        attr = getattr(main_views, name)
        # Only import functions and classes
        if callable(attr):
            # Add it to the current namespace
            globals()[name] = attr