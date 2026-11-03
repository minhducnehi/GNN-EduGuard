using GNN_EduGuard.Models;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers
{
    public class StudentsController : Controller
    {
        private readonly IStudentService _studentService;

        public StudentsController(IStudentService studentService)
        {
            _studentService = studentService;
        }

        // GET: /Students
        public IActionResult Index(string? search, RiskLevel? riskFilter)
        {
            ViewBag.CurrentSearch = search;
            ViewBag.CurrentFilter = riskFilter;

            var students = _studentService.GetAllStudents(search, riskFilter);
            return View(students);
        }

        // GET: /Students/Details/1
        public IActionResult Details(int id)
        {
            var detail = _studentService.GetStudentRiskDetail(id);
            if (detail == null)
            {
                return NotFound();
            }

            return View(detail);
        }

        // POST: /Students/ReEvaluate/1
        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult ReEvaluate(int id)
        {
            _studentService.ReEvaluateStudentRisk(id);
            TempData["SuccessMessage"] = $"Đã kích hoạt mô hình GNN đánh giá lại sinh viên ID #{id} thành công!";
            return RedirectToAction(nameof(Details), new { id });
        }
    }
}
