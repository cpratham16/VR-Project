import pytest
import uuid
from fastapi import HTTPException
from app.models.user import User
from app.models.anonymized import RegionalAggregate
from app.core.database import AsyncSessionLocal
from app.api.v1.admin import get_overview, get_trend, export_analytics
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_small_cohort_suppression_and_jurisdiction():
    admin_ca_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        # Create state-scoped admin for California
        admin_ca = User(
            id=admin_ca_id,
            email=f"admin_ca_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="pw",
            role="admin",
            state="California"
        )
        db.add(admin_ca)

        # 1. Create small cohort (< 10 patients) in California
        small_aggregate = RegionalAggregate(
            region="California",
            period="2026-08",
            total_patients=5,
            screening_count=5,
            phq9_minimal=2,
            phq9_mild=3,
            risk_alert_count=1
        )
        # 2. Create normal cohort (>= 10 patients) in New York
        normal_aggregate = RegionalAggregate(
            region="New York",
            period="2026-08",
            total_patients=45,
            screening_count=40,
            phq9_minimal=20,
            phq9_mild=10,
            phq9_moderate=10,
            risk_alert_count=2
        )
        db.add_all([small_aggregate, normal_aggregate])
        await db.commit()

        # Test small-cohort suppression for CA admin on CA region
        trend_ca = await get_trend(region="California", db=db, current_admin=admin_ca)
        assert len(trend_ca) >= 1
        ca_record = [r for r in trend_ca if r["period"] == "2026-08"][0]
        assert ca_record["suppressed"] is True
        assert ca_record["total_patients"] == "insufficient_data (<10)"
        assert ca_record["screening_count"] is None
        assert ca_record["phq9_minimal"] is None

        # Test Role-Scoped Jurisdiction Security: CA admin attempting to query New York
        with pytest.raises(HTTPException) as exc_info:
            await get_trend(region="New York", db=db, current_admin=admin_ca)
        assert exc_info.value.status_code == 403
        assert "restricted to 'California'" in exc_info.value.detail

        # Test CSV Export
        csv_resp = await export_analytics(format="csv", region="California", db=db, current_admin=admin_ca)
        assert csv_resp.media_type == "text/csv"
        assert b"region,period,total_patients" in csv_resp.body
        assert b"California" in csv_resp.body

        # Test PDF Export
        pdf_resp = await export_analytics(format="pdf", region="California", db=db, current_admin=admin_ca)
        assert pdf_resp.media_type == "application/pdf"
        assert pdf_resp.body.startswith(b"%PDF-1.4")

        # Cleanup
        await db.delete(small_aggregate)
        await db.delete(normal_aggregate)
        await db.delete(admin_ca)
        await db.commit()
