"""
이메일 전송 서비스

SMTP를 통해 이메일을 발송합니다.
"""

import smtplib
import logging
import random
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스"""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        image_path: str,
        image_filename: str = "image.png"
    ) -> bool:
        """
        이메일 발송 (이미지 첨부)

        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            html_body: HTML 본문 (cid:postcard_image로 이미지 참조)
            image_path: 첨부할 이미지 파일 경로
            image_filename: 첨부파일명

        Returns:
            발송 성공 여부

        Raises:
            Exception: 이메일 발송 실패 시
        """
        try:
            # MIMEMultipart 생성 (related: 인라인 이미지 지원)
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # HTML 파트 추가
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

            # 이미지 읽기
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")

            with open(path, 'rb') as f:
                image_data = f.read()

            # 인라인 이미지 추가 (HTML에서 cid:postcard_image로 참조)
            image = MIMEImage(image_data)
            image.add_header('Content-ID', '<postcard_image>')
            image.add_header('Content-Disposition', 'inline', filename=path.name)
            msg.attach(image)

            # 첨부파일로도 추가 (다운로드 가능하도록)
            image_attachment = MIMEImage(image_data)
            image_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=image_filename
            )
            msg.attach(image_attachment)

            # SMTP 서버 연결 및 전송
            logger.info(f"Sending email to {to_email} (Subject: {subject})")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS 암호화
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise

    def _get_postcard_email_html(self, greeting: str, subtitle_message: str) -> str:
        """엽서 이메일 HTML 템플릿 생성"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                @keyframes float {{
                    0%, 100% {{ transform: translateY(0px); }}
                    50% {{ transform: translateY(-5px); }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Malgun Gothic', '맑은 고딕', 'Apple SD Gothic Neo', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); min-height: 100vh; padding: 40px 20px;">
            
            <!-- 우편함 배경 효과 -->
            <div style="max-width: 700px; margin: 0 auto; perspective: 1000px;">
                
                <!-- 실제 엽서 카드 -->
                <div style="background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1); position: relative; animation: fadeIn 0.8s ease-out; transform: rotate(-0.5deg);">

                    <!-- 수신자 정보 (엽서 상단) -->
                    <div style="padding: 30px 40px 20px; background: linear-gradient(180deg, rgba(255,255,255,0.8) 0%, transparent 100%);">
                        <div style="display: inline-block; padding: 8px 20px; background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; border-radius: 0 8px 8px 0; margin-bottom: 10px;">
                            <p style="margin: 0; color: #667eea; font-size: 12px; font-weight: bold; letter-spacing: 2px;">제주바당우체국</p>
                        </div>
                        <h2 style="margin: 10px 0 5px; color: #2d3748; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">{greeting}</h2>
                        <p style="margin: 0; color: #718096; font-size: 14px; font-style: italic;">{subtitle_message}</p>
                    </div>

                    <!-- 엽서 이미지 (메인 컨텐츠) -->
                    <div style="padding: 20px 40px 30px;">
                        <div style="position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.6); background: white;">
                            <!-- 종이 텍스처 효과 -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.02) 2px, rgba(0,0,0,0.02) 4px); pointer-events: none; z-index: 1;"></div>
                            
                            <img src="cid:postcard_image" alt="제주에서 온 엽서" style="width: 100%; height: auto; display: block; position: relative; z-index: 0; border-radius: 12px;">
                            
                            <!-- 사진 테두리 효과 -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; pointer-events: none; z-index: 2;"></div>
                        </div>
                        
                    </div>

                    <!-- 점선 (엽서 하단 구분선) -->
                    <div style="margin: 0 40px; border-top: 2px dashed rgba(0,0,0,0.1);"></div>

                    <!-- 푸터 -->
                    <div style="padding: 25px 40px 30px; background: linear-gradient(180deg, transparent 0%, rgba(248,249,250,0.8) 100%);">
                        <div style="text-align: center;">
                            <p style="margin: 0; color: #a0aec0; font-size: 11px; line-height: 1.5;">
                                ⓒ 제주바당우체국 · 나눔글꼴 사용 (규리의 일기, 네이버 제공)
                            </p>
                        </div>
                    </div>

                    <!-- 종이 그림자 효과 -->
                    <div style="position: absolute; bottom: -8px; left: 20px; right: 20px; height: 8px; background: rgba(0,0,0,0.1); filter: blur(8px); border-radius: 50%; z-index: -1;"></div>
                </div>
            </div>
        </body>
        </html>
        """
        return html


    async def send_postcard_email(
        self,
        to_email: str,
        to_name: Optional[str],
        postcard_image_path: str,
        sender_name: Optional[str] = None,
        subject: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """
        엽서 이메일 발송 (래퍼 메서드)
        
        Args:
            to_email: 수신자 이메일
            to_name: 수신자 이름
            postcard_image_path: 엽서 이미지 경로
            sender_name: 발신자 이름
            subject: 이메일 제목 (기본값: "제주에서 온 엽서")
            custom_message: 사용자 정의 메시지
        
        Returns:
            발송 성공 여부
        """
        # 랜덤 제목 리스트
        random_subjects = [
            "혼저 옵서예, 제주에서 카드 하나 보냅니다게!",
            "제주 바람이 살랑살랑~ 그 바람에 실려서 엽서 하나 날아갑주게!",
            "오늘도 촘 이쁘게 지내라예? 제주서 정든 마음 보내봅디다~",
            "하영 보고싶수다! 제주 하늘빛이랑 같이 보냅니다게.",
            "귤향 폴폴~ 제주서 달큰한 소식 하나 들려줍써!"
        ]
        
        # 랜덤 메시지 리스트
        random_messages = [
            "제주 바당바람에 마음 한 줌 싣어 보내드립주게!",
            "제주서 건진 따순 마음, 바람 타고 살짝 보내봅디다.",
            "바당 우체부가 챙겨온 설레는 마음 한 통, 혼저 받아주게!",
            "제주 물빛처럼 고운 마음 실어 바당우체부가 배달합주게"
        ]
        
        # 이메일 제목 설정 (랜덤 또는 사용자 지정)
        if not subject:
            subject = random.choice(random_subjects)
        
        logger.info(f"Preparing postcard email for {to_email} (to: {to_name or 'N/A'}, from: {sender_name or 'N/A'})")
        
        # HTML 생성
        greeting = f"{to_name}님께" if to_name else "소중한 당신에게"
        subtitle_message = custom_message or random.choice(random_messages)
        
        html_body = self._get_postcard_email_html(greeting, subtitle_message)
        
        # 이메일 발송
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            image_path=postcard_image_path,
            image_filename="postcard.png"
        )
