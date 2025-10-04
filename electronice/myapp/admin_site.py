from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class ElectronicsStoreAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = _('Electronics Store Admin')

    # Text to put in each page's <h1> (and above login form).
    site_header = _('Electronics Store Administration')

    # Text to put at the top of the admin index page.
    index_title = _('Store Administration')

    # URL for the "View site" link at the top of each admin page.
    site_url = '/'

admin_site = ElectronicsStoreAdminSite(name='admin') 