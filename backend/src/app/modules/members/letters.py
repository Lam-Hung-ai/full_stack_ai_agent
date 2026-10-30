"""Invitation letter."""

from app.common.email import Letter
from app.config.settings import get_settings


def invitation_letter(
    *, to: str, organization_name: str, inviter_name: str, token: str
) -> Letter:
    settings = get_settings()
    link = f"{settings.frontend_url}/invitations?token={token}"
    return Letter(
        to=to,
        subject=f"Lời mời tham gia {organization_name}",
        body=(
            f"{inviter_name} mời bạn tham gia tổ chức {organization_name}.\n\n"
            "Mở liên kết dưới đây để nhận lời mời:\n\n"
            f"{link}\n\n"
            f"Lời mời hết hạn sau {settings.invitation_days} ngày. "
            "Nếu bạn không mong đợi thư này, hãy bỏ qua.\n"
        ),
        purpose="invitation",
    )
