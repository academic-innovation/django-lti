from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import EmbedDomain
from .utils import get_embed_cache, get_embed_cache_key


@receiver((post_delete, post_save), sender=EmbedDomain)
def clear_domain_cache(sender, instance, **kwargs):
    """Clears a registration's domain cache when domains are saved or deleted.

    The cache is cleared after the transaction commits, so a concurrent request
    can't re-cache the old domains in between.
    """
    key = get_embed_cache_key(instance.registration_id)
    transaction.on_commit(lambda: get_embed_cache().delete(key))
