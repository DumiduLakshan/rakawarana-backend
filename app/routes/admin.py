import logging

from fastapi import APIRouter, Depends

from app.services.posts_service import delete_post, list_unverified_posts, verify_post
from app.utils.auth import require_admin_token
from app.utils.supabase_client import get_supabase

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_token)])
logger = logging.getLogger(__name__)


@router.get("/posts/unverified", summary="List unverified posts with images (admin)")
def get_unverified_posts(supabase_client=Depends(get_supabase)):
    return list_unverified_posts(supabase_client)


@router.post("/posts/{post_id}/verify", summary="Verify a post by id (admin)")
def verify_rescue_post(post_id: str, supabase_client=Depends(get_supabase)):
    return verify_post(supabase_client, post_id)


@router.delete("/posts/{post_id}", summary="Delete a post by id (admin)")
def delete_rescue_post(post_id: str, supabase_client=Depends(get_supabase)):
    delete_post(supabase_client, post_id)
    return {"message": "Post deleted", "post_id": post_id}
