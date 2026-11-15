using GNN_EduGuard.Models;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers
{
    [Authorize]
    public class StudentsController : Controller
    {
        private readonly IStudentService _studentService;
        private readonly IEmailService _emailService;
        private readonly IConfiguration _configuration;

        public StudentsController(
            IStudentService studentService,
            IEmailService emailService,
            IConfiguration configuration)
        {
            _studentService = studentService;
            _emailService = emailService;
            _configuration = configuration;
        }

        // GET: /Students
        [Authorize(Roles = "Admin,Advisor")]
        public async Task<IActionResult> Index(string? search, RiskLevel? riskFilter)
        {
            ViewBag.CurrentSearch = search;
            ViewBag.CurrentFilter = riskFilter;
            ViewBag.SmtpEmail = _configuration["Smtp:Email"] ?? string.Empty;
            ViewBag.HasSmtpPassword = !string.IsNullOrWhiteSpace(_configuration["Smtp:AppPassword"]);

            var students = User.FilterByRoleScope(await _studentService.GetAllStudentsAsync(search, riskFilter));
            return View(students);
        }

        // GET: /Students/ExportCsv
        [Authorize(Roles = "Admin,Advisor")]
        public async Task<IActionResult> ExportCsv(string? search, RiskLevel? riskFilter)
        {
            if (User.IsInRole("Admin"))
            {
                var csvBytes = await _studentService.ExportStudentsCsvAsync(search, riskFilter);
                var adminFileName = $"BaoCao_CanhBaoHocVu_DiemDanh_GNN_{DateTime.Now:yyyyMMdd_HHmm}.csv";
                return File(csvBytes, "text/csv; charset=utf-8", adminFileName);
            }

            var scopedStudents = User.FilterByRoleScope(await _studentService.GetAllStudentsAsync(search, riskFilter));
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("MaSV,HoTen,Email,Lop,GPATruoc,DiemDanh,TyLeChuyenCan(%),VLEClicks,NopMuon(%),DiemTB,XacSuatNguyCo(%),MucDo,YeuToChinh");
            foreach (var s in scopedStudents)
            {
                var levelVi = s.RiskLevel switch
                {
                    RiskLevel.HighRisk => "Nguy cơ cao",
                    RiskLevel.Moderate => "Nguy cơ vừa",
                    _ => "An toàn"
                };
                var safeReason = (s.TopRiskFactor ?? string.Empty).Replace("\"", "\"\"");
                sb.AppendLine($"{s.StudentCode},\"{s.FullName}\",{s.Email},{s.ClassName},{s.GpaBefore:F2},{s.AttendedSessions}/{s.TotalSessions},{(int)(s.AttendanceRate * 100)},{s.TotalVleClicks},{(int)(s.LateSubmissionRate * 100)},{s.AssignmentAverageScore:F1},{(int)(s.RiskProbability * 100)},\"{levelVi}\",\"{safeReason}\"");
            }
            var bom = System.Text.Encoding.UTF8.GetPreamble();
            var bodyBytes = System.Text.Encoding.UTF8.GetBytes(sb.ToString());
            var scopedBytes = bom.Concat(bodyBytes).ToArray();
            var fileName = $"BaoCao_CanhBaoHocVu_TheoLop_GNN_{DateTime.Now:yyyyMMdd_HHmm}.csv";
            return File(scopedBytes, "text/csv; charset=utf-8", fileName);
        }

        // POST: /Students/SendBulkWarningEmails
        [HttpPost]
        [Authorize(Roles = "Admin,Advisor")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> SendBulkWarningEmails(
            string? search,
            RiskLevel? riskFilter,
            string? advisorNote)
        {
            var students = User.FilterByRoleScope(await _studentService.GetAllStudentsAsync(search, riskFilter));
            if (!students.Any())
            {
                TempData["ErrorMessage"] = "Không có sinh viên nào trong danh sách hiện tại để gửi email cảnh báo.";
                return RedirectToAction(nameof(Index), new { search, riskFilter });
            }

            var result = await _emailService.SendBulkWarningEmailsAsync(students, advisorNote);

            if (result.SentCount > 0 && result.FailedCount == 0)
            {
                TempData["SuccessMessage"] = $"Đã gửi Gmail cảnh báo thành công tới {result.SentCount}/{result.TotalTargets} sinh viên!";
            }
            else if (result.SentCount > 0 && result.FailedCount > 0)
            {
                var firstErr = result.Errors.FirstOrDefault() ?? string.Empty;
                TempData["ErrorMessage"] = $"Đã gửi {result.SentCount}/{result.TotalTargets} email, thất bại {result.FailedCount}. Chi tiết: {firstErr}";
            }
            else
            {
                var firstErr = result.Errors.FirstOrDefault() ?? "Không thể gửi email qua Gmail SMTP.";
                TempData["ErrorMessage"] = $"Gửi Gmail thất bại ({result.FailedCount}/{result.TotalTargets}): {firstErr}";
            }

            return RedirectToAction(nameof(Index), new { search, riskFilter });
        }

        private async Task<bool> CanManageStudentAsync(int studentId)
        {
            var student = await _studentService.GetStudentByIdAsync(studentId);
            return student != null && User.CanAccessStudent(student);
        }

        // GET: /Students/Details/1
        public async Task<IActionResult> Details(int id)
        {
            if (User.IsInRole("Student"))
            {
                var allowedId = User.GetStudentId();
                if (id != allowedId)
                {
                    TempData["ErrorMessage"] = "Vì lý do bảo mật quyền riêng tư, sinh viên chỉ được xem lộ trình học tập cá nhân của chính mình.";
                    return RedirectToAction(nameof(Details), new { id = allowedId });
                }
            }

            var detail = await _studentService.GetStudentRiskDetailAsync(id);
            if (detail == null)
            {
                return NotFound();
            }

            if (!User.CanAccessStudent(detail.Student))
            {
                TempData["ErrorMessage"] = $"Bạn chỉ được phép xem sinh viên thuộc lớp mình phụ trách ({string.Join(", ", User.GetAssignedClasses())}).";
                return RedirectToAction(nameof(Index));
            }

            return View(detail);
        }

        // POST: /Students/ReEvaluate/1
        [HttpPost]
        [Authorize(Roles = "Admin,Advisor")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> ReEvaluate(int id)
        {
            if (!await CanManageStudentAsync(id))
            {
                TempData["ErrorMessage"] = "Bạn không có quyền thao tác trên sinh viên thuộc lớp khác.";
                return RedirectToAction(nameof(Index));
            }

            await _studentService.ReEvaluateStudentRiskAsync(id);
            TempData["SuccessMessage"] = $"Đã làm mới bộ nhớ đệm XAI và chạy lại mô hình HGT (kèm dữ liệu điểm danh) cho sinh viên ID #{id}!";
            return RedirectToAction(nameof(Details), new { id });
        }

        // POST: /Students/UpdateAttendance
        [HttpPost]
        [Authorize(Roles = "Admin,Advisor")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> UpdateAttendance(int studentId, int attendedSessions, int totalSessions = 9)
        {
            if (!await CanManageStudentAsync(studentId))
            {
                TempData["ErrorMessage"] = "Bạn không có quyền điểm danh sinh viên thuộc lớp khác.";
                return RedirectToAction(nameof(Index));
            }

            attendedSessions = Math.Clamp(attendedSessions, 0, Math.Max(1, totalSessions));
            await _studentService.UpdateStudentAttendanceAsync(studentId, attendedSessions, totalSessions);

            var student = await _studentService.GetStudentByIdAsync(studentId);
            var ratePct = student != null ? (int)(student.AttendanceRate * 100) : 0;
            var probPct = student != null ? (int)(student.RiskProbability * 100) : 0;
            var absent = Math.Max(0, totalSessions - attendedSessions);

            TempData["SuccessMessage"] = $"Đã cập nhật Điểm danh: Có mặt {attendedSessions}/{totalSessions} buổi ({ratePct}%, vắng {absent} buổi) -> Mô hình GNN đã dự báo lại Xác suất nguy cơ mới: {probPct}%!";
            return RedirectToAction(nameof(Details), new { id = studentId });
        }

        // POST: /Students/AddIntervention
        [HttpPost]
        [Authorize(Roles = "Admin,Advisor")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> AddIntervention(int studentId, string actionType, string notes)
        {
            if (!await CanManageStudentAsync(studentId))
            {
                TempData["ErrorMessage"] = "Bạn không có quyền ghi nhật ký cho sinh viên thuộc lớp khác.";
                return RedirectToAction(nameof(Index));
            }

            if (string.IsNullOrWhiteSpace(notes))
            {
                TempData["ErrorMessage"] = "Vui lòng nhập nội dung ghi chú can thiệp học vụ.";
                return RedirectToAction(nameof(Details), new { id = studentId });
            }

            var advisorName = User.Identity?.Name ?? "CVHT. Nguyễn Minh Đức";
            await _studentService.AddInterventionLogAsync(studentId, advisorName, actionType, notes);
            TempData["SuccessMessage"] = "Đã lưu nhật ký can thiệp học vụ vào hồ sơ theo dõi sinh viên!";
            return RedirectToAction(nameof(Details), new { id = studentId });
        }
    }
}
