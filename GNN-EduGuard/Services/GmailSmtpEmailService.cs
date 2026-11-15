using System.Net;
using System.Net.Mail;
using System.Text;
using GNN_EduGuard.Models;

namespace GNN_EduGuard.Services
{
    public class GmailSmtpEmailService : IEmailService
    {
        private readonly IConfiguration _configuration;
        private readonly ILogger<GmailSmtpEmailService> _logger;

        public GmailSmtpEmailService(IConfiguration configuration, ILogger<GmailSmtpEmailService> logger)
        {
            _configuration = configuration;
            _logger = logger;
        }

        public async Task<BulkEmailResult> SendBulkWarningEmailsAsync(
            IEnumerable<Student> students,
            string? advisorNote = null)
        {
            var studentList = students.ToList();
            var result = new BulkEmailResult { TotalTargets = studentList.Count };

            var host = _configuration["Smtp:Host"] ?? "smtp.gmail.com";
            var port = int.TryParse(_configuration["Smtp:Port"], out var parsedPort) ? parsedPort : 587;
            var senderName = _configuration["Smtp:SenderName"] ?? "GNN-EduGuard Cố vấn Học tập";
            var senderEmail = (_configuration["Smtp:Email"] ?? string.Empty).Trim();
            var appPassword = (_configuration["Smtp:AppPassword"] ?? string.Empty).Replace(" ", string.Empty).Trim();

            if (string.IsNullOrWhiteSpace(senderEmail) || string.IsNullOrWhiteSpace(appPassword))
            {
                result.FailedCount = studentList.Count;
                result.Errors.Add("Chưa cấu hình Mật khẩu ứng dụng Gmail (Smtp__AppPassword) trong file .env.");
                return result;
            }

            using var smtpClient = new SmtpClient(host, port)
            {
                EnableSsl = true,
                DeliveryMethod = SmtpDeliveryMethod.Network,
                UseDefaultCredentials = false,
                Credentials = new NetworkCredential(senderEmail, appPassword),
                Timeout = 20000
            };

            foreach (var student in studentList)
            {
                var targetEmail = student.Email?.Trim();
                if (string.IsNullOrWhiteSpace(targetEmail))
                {
                    result.FailedCount++;
                    result.Errors.Add($"{student.StudentCode} ({student.FullName}): Chưa có email đăng ký.");
                    continue;
                }

                try
                {
                    var subject = $"[GNN-EduGuard] Cảnh báo Học vụ & Chuyên cần - {student.FullName} ({student.StudentCode})";
                    var htmlBody = BuildHtmlWarningBody(student, advisorNote);

                    using var message = new MailMessage
                    {
                        From = new MailAddress(senderEmail, senderName, Encoding.UTF8),
                        Subject = subject,
                        SubjectEncoding = Encoding.UTF8,
                        Body = htmlBody,
                        BodyEncoding = Encoding.UTF8,
                        IsBodyHtml = true
                    };
                    message.To.Add(new MailAddress(targetEmail, student.FullName, Encoding.UTF8));

                    await smtpClient.SendMailAsync(message);
                    result.SentCount++;
                }
                catch (Exception ex)
                {
                    result.FailedCount++;
                    _logger.LogWarning(ex, "Failed to send warning email to {StudentCode} ({Email})", student.StudentCode, targetEmail);
                    result.Errors.Add($"{student.StudentCode} ({targetEmail}): {ex.Message}");
                }
            }

            return result;
        }

        private static string BuildHtmlWarningBody(Student student, string? advisorNote)
        {
            var attPct = (int)Math.Round(student.AttendanceRate * 100);
            var latePct = (int)Math.Round(student.LateSubmissionRate * 100);
            var riskPct = (int)Math.Round(student.RiskProbability * 100);
            var riskLabel = student.RiskLevel switch
            {
                RiskLevel.HighRisk => "Nguy cơ cao",
                RiskLevel.Moderate => "Nguy cơ vừa",
                _ => "An toàn"
            };
            var riskColor = student.RiskLevel switch
            {
                RiskLevel.HighRisk => "#dc2626",
                RiskLevel.Moderate => "#d97706",
                _ => "#16a34a"
            };
            var topFactor = string.IsNullOrWhiteSpace(student.TopRiskFactor)
                ? "Cần theo dõi thêm chuyên cần và tiến độ học tập"
                : WebUtility.HtmlEncode(student.TopRiskFactor);

            var noteSection = string.IsNullOrWhiteSpace(advisorNote)
                ? string.Empty
                : $@"<div style=""margin-top:16px;padding:12px 14px;background:#eff6ff;border-left:4px solid #2563eb;border-radius:6px;"">
                        <strong style=""color:#1e40af;"">Lời nhắn từ Cố vấn Học tập:</strong><br/>
                        <span>{WebUtility.HtmlEncode(advisorNote.Trim()).Replace("\n", "<br/>")}</span>
                     </div>";

            return $@"
<div style=""font-family:Segoe UI,Arial,sans-serif;max-width:620px;margin:0 auto;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;color:#1f2937;"">
  <div style=""background:#dc2626;color:#ffffff;padding:16px 22px;"">
    <h2 style=""margin:0;font-size:18px;"">Cảnh báo Học vụ &amp; Chuyên cần — GNN-EduGuard</h2>
  </div>
  <div style=""padding:20px 22px;line-height:1.6;"">
    <p style=""margin-top:0;"">Kính gửi sinh viên <strong>{WebUtility.HtmlEncode(student.FullName)}</strong> (MSSV: <strong>{WebUtility.HtmlEncode(student.StudentCode)}</strong> - Lớp: <strong>{WebUtility.HtmlEncode(student.ClassName)}</strong>),</p>
    <p>Hệ thống Cảnh báo Sớm <strong>GNN-EduGuard</strong> ghi nhận tình hình học tập hiện tại của bạn đang ở mức:
      <span style=""display:inline-block;padding:2px 10px;border-radius:999px;background:{riskColor};color:#fff;font-weight:600;font-size:13px;"">{riskLabel} ({riskPct}%)</span>
    </p>
    <table style=""width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;"">
      <tr style=""background:#f9fafb;""><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">Chuyên cần (Điểm danh)</td><td style=""padding:8px 12px;border:1px solid #e5e7eb;font-weight:600;"">{student.AttendedSessions}/{student.TotalSessions} buổi ({attPct}%), vắng {student.AbsentSessions} buổi</td></tr>
      <tr><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">GPA trước</td><td style=""padding:8px 12px;border:1px solid #e5e7eb;font-weight:600;"">{student.GpaBefore:F2}</td></tr>
      <tr style=""background:#f9fafb;""><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">Tương tác học liệu VLE</td><td style=""padding:8px 12px;border:1px solid #e5e7eb;font-weight:600;"">{student.TotalVleClicks} clicks</td></tr>
      <tr><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">Tỷ lệ nộp bài muộn</td><td style=""padding:8px 12px;border:1px solid #e5e7eb;font-weight:600;"">{latePct}%</td></tr>
      <tr style=""background:#f9fafb;""><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">Yếu tố rủi ro chính</td><td style=""padding:8px 12px;border:1px solid #e5e7eb;"">{topFactor}</td></tr>
    </table>
    {noteSection}
    <p style=""margin-top:16px;font-size:13px;color:#b91c1c;background:#fef2f2;padding:10px 12px;border-radius:6px;"">
      <strong>Lưu ý quy chế:</strong> Sinh viên vắng quá 20% số buổi học sẽ có nguy cơ bị cấm thi cuối kỳ. Đề nghị bạn sớm liên hệ hoặc lên gặp Cố vấn Học tập để được hỗ trợ kịp thời.
    </p>
    <p style=""margin-bottom:0;color:#4b5563;font-size:13px;"">Trân trọng,<br/><strong>Cố vấn Học tập - Hệ thống GNN-EduGuard</strong></p>
  </div>
</div>";
        }
    }
}
