from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.services.email_service import deliver_campaign_email
from app.services.notification_service import dispatch_content_notification
from app.models.user import User
from app.models.campaign import EmailCampaign, EmailRecipient
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignDetailResponse, RecipientResponse, UnsubscribeUpdate
)

router = APIRouter(prefix="", tags=["campaigns"])

@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_in: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    campaign = EmailCampaign(
        **campaign_in.model_dump(),
        created_by=admin.id,
        status="draft"
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = select(EmailCampaign)
    if status_filter:
        query = query.where(EmailCampaign.status == status_filter)
    query = query.order_by(EmailCampaign.created_at.desc())
    result = await db.execute(query)
    campaigns = result.scalars().all()

    output = []
    for c in campaigns:
        # Count recipients
        rec_count_res = await db.execute(select(EmailRecipient).where(EmailRecipient.campaign_id == c.id))
        recs = rec_count_res.scalars().all()
        resp = CampaignResponse.model_validate(c)
        resp.recipient_count = len(recs)
        output.append(resp)
    return output

@router.get("/campaigns/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    c_res = await db.execute(select(EmailCampaign).where(EmailCampaign.id == campaign_id))
    campaign = c_res.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    rec_res = await db.execute(select(EmailRecipient).where(EmailRecipient.campaign_id == campaign_id))
    recipients = rec_res.scalars().all()

    resp = CampaignDetailResponse.model_validate(campaign)
    resp.recipients = [RecipientResponse.model_validate(r) for r in recipients]
    resp.recipient_count = len(recipients)
    return resp

@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_in: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    c_res = await db.execute(select(EmailCampaign).where(EmailCampaign.id == campaign_id))
    campaign = c_res.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = campaign_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    await db.commit()
    await db.refresh(campaign)
    return campaign

@router.post("/campaigns/{campaign_id}/send", response_model=CampaignDetailResponse)
async def send_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    c_res = await db.execute(select(EmailCampaign).where(EmailCampaign.id == campaign_id))
    campaign = c_res.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == "sent":
        raise HTTPException(status_code=400, detail="Campaign has already been sent")

    # Select target users based on non-clinical audience criteria & filter out unsubscribed users (N8 safeguard)
    user_query = select(User).where(User.is_active == True).where(User.unsubscribed_from_communications == False)
    if campaign.audience_type == "students":
        user_query = user_query.where(User.role == "patient")
    elif campaign.audience_type == "doctors":
        user_query = user_query.where(User.role == "doctor")
    elif campaign.audience_type == "admins":
        user_query = user_query.where(User.role == "admin")

    users_res = await db.execute(user_query)
    target_users = users_res.scalars().all()

    now = datetime.utcnow()
    recipients = []
    for u in target_users:
        delivery_status, err = deliver_campaign_email(u.email, campaign.subject, campaign.body_html)
        rec = EmailRecipient(
            campaign_id=campaign.id,
            user_id=u.id,
            email=u.email,
            status=delivery_status,
            sent_at=now if delivery_status != "failed" else None,
            error_message=err
        )
        db.add(rec)
        recipients.append(rec)

    campaign.status = "sent"
    campaign.sent_at = now

    if "in_app" in campaign.delivery_channels.lower():
        await dispatch_content_notification(
            db,
            title=campaign.title,
            content_type="announcement",
            link_url="/patient/library",
            recipient_role=campaign.audience_type if campaign.audience_type != "all" else "patient"
        )

    await db.commit()
    await db.refresh(campaign)

    resp = CampaignDetailResponse.model_validate(campaign)
    resp.recipients = [RecipientResponse.model_validate(r) for r in recipients]
    resp.recipient_count = len(recipients)
    return resp

@router.post("/patient/unsubscribe", response_model=dict)
async def update_unsubscribe_status(
    opt_in: UnsubscribeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.unsubscribed_from_communications = opt_in.unsubscribed
    await db.commit()
    return {"unsubscribed": current_user.unsubscribed_from_communications}

@router.get("/patient/unsubscribe", response_model=dict)
async def get_unsubscribe_status(
    current_user: User = Depends(get_current_user)
):
    return {"unsubscribed": current_user.unsubscribed_from_communications}
