import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import re
import logging
from datetime import datetime
from typing import List, Optional
import mimetypes  # 导入 mimetypes 模块
import sys
import urllib.parse
from email.header import Header
# 修改导入路径
from .config import EMAIL_CONFIG

class EmailSender:
    def __init__(self):
        self.smtp_server = EMAIL_CONFIG['smtp_server']
        self.smtp_port = EMAIL_CONFIG['smtp_port']
        self.sender_email = EMAIL_CONFIG['sender_email']
        self.sender_password = EMAIL_CONFIG['sender_password']
        self.user_groups = EMAIL_CONFIG.get('user_groups', {})
        self._setup_logging()

    def _setup_logging(self):
        """配置日志记录"""
        log_dir = os.path.join('logs', 'mail')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'mail_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _resolve_recipients(self, recipients: List[str]) -> List[str]:
        """解析收件人列表，处理用户组"""
        resolved_emails = set()
        
        for recipient in recipients:
            if recipient in self.user_groups:
                resolved_emails.update(self.user_groups[recipient])
            else:
                if self._validate_email(recipient):
                    resolved_emails.add(recipient)
        
        return list(resolved_emails)

    def _validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    def send_email(
        self,
        subject: str,
        recipients: List[str],
        body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题（必填）
            recipients: 收件人列表（必填）
            body: 邮件正文（可选）
            cc: 抄送人列表（可选）
            attachments: 附件路径列表或MIMEBase对象列表（可选）
        """
        if not subject:
            raise ValueError("邮件主题不能为空")
            
        if not recipients:
            raise ValueError("收件人不能为空")

        # 解析收件人和抄送人
        to_emails = self._resolve_recipients(recipients)
        cc_emails = self._resolve_recipients(cc) if cc else []

        if not to_emails:
            raise ValueError("未找到有效的收件人邮箱")

        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)

        # 添加正文
        if body:
            msg.attach(MIMEText(body, 'plain'))

        # 添加附件
        if attachments:
            for attachment_item in attachments:
                try:
                    # 检查是否为MIMEBase对象
                    if isinstance(attachment_item, MIMEBase):
                        # 直接添加MIMEBase对象
                        msg.attach(attachment_item)
                    else:
                        # 假设是文件路径
                        file_path = attachment_item
                        with open(file_path, 'rb') as attachment:
                            # 推断附件的 MIME 类型
                            mime_type, encoding = mimetypes.guess_type(file_path)
                            if mime_type is None:
                                mime_type = 'application/octet-stream'
                            
                            maintype, subtype = mime_type.split('/', 1)
                            part = MIMEBase(maintype, subtype)
                            part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        
                        # 修改这里，使用更简单的方式处理中文文件名
                        filename = os.path.basename(file_path)
                        # 直接使用RFC 5987编码方式，不使用Header类
                        encoded_filename = urllib.parse.quote(filename)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                        )
                        
                        msg.attach(part)
                except Exception as e:
                    logging.error(f"无法添加附件 {attachment_item}: {e}")
                    return False

        # 发送邮件
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    to_emails + cc_emails,
                    msg.as_string()
                )
            
            # 记录成功日志
            logging.info(
                f"邮件发送成功\n"
                f"主题: {subject}\n"
                f"收件人: {', '.join(to_emails)}\n"
                f"抄送人: {', '.join(cc_emails) if cc_emails else '无'}"
            )
            return True
            
        except Exception as e:
            # 记录失败日志
            logging.error(
                f"邮件发送失败\n"
                f"主题: {subject}\n"
                f"收件人: {', '.join(to_emails)}\n"
                f"抄送人: {', '.join(cc_emails) if cc_emails else '无'}\n"
                f"错误信息: {str(e)}"
            )
            raise RuntimeError(f"邮件发送失败: {str(e)}")

# 示例用法
if __name__ == "__main__":
    sender = EmailSender()
    
    try:
        success = sender.send_email(
            subject="测试邮件",
            recipients=["COI", "819265786@qq.com"],
            cc=["ijla16827@163.com"],
            body="这是一封测试邮件"
        )
        
        if success:
            print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}") 