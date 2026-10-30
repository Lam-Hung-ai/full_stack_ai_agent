"""Account letters: email verification and password reset."""

from typing import Literal

from app.common.email import Letter
from app.config.settings import get_settings

type Purpose = Literal["email_verify", "password_reset"]


def account_letter(*, to: str, name: str, purpose: Purpose, token: str) -> Letter:
    settings = get_settings()
    if purpose == "email_verify":
        link = f"{settings.frontend_url}/verify-email?token={token}"
        return Letter(
            to=to,
            subject="Xác minh email",
            body=(
                f"Chào {name},\n\n"
                "Mở liên kết dưới đây để xác minh email của bạn:\n\n"
                f"{link}\n\n"
                f"Liên kết hết hạn sau {settings.email_verification_hours} giờ. "
                "Nếu bạn không tạo tài khoản, hãy bỏ qua thư này.\n"
            ),
            purpose=purpose,
        )
    link = f"{settings.frontend_url}/reset-password?token={token}"
    return Letter(
        to=to,
        subject="Đặt lại mật khẩu",
        body=(
            f"Chào {name},\n\n"
            "Mở liên kết dưới đây để đặt mật khẩu mới:\n\n"
            f"{link}\n\n"
            f"Liên kết hết hạn sau {settings.password_reset_minutes} phút. "
            "Đặt lại mật khẩu sẽ đăng xuất mọi phiên đang mở. "
            "Nếu bạn không yêu cầu, hãy bỏ qua thư này.\n"
        ),
        purpose=purpose,
    )
