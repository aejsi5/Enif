from rest_framework import permissions
import requests
from .models import Whitelist


class WhitelistPermission(permissions.BasePermission):
    message ="Host not allowed"
    """
    Global permission check for whitelisted Hosts.
    """
    def has_permission(self, request, view):
        domain = request.headers.get('Host')
        whitelisted = Whitelist.objects.filter(Host=domain, D=False).exists()
        return whitelisted
