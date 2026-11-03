using GNN_EduGuard.Models;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers.Api
{
    [ApiController]
    [Route("api/[controller]")]
    public class PredictionsApiController : ControllerBase
    {
        private readonly IStudentService _studentService;

        public PredictionsApiController(IStudentService studentService)
        {
            _studentService = studentService;
        }

        // GET: api/predictionsapi/dashboard
        [HttpGet("dashboard")]
        public IActionResult GetDashboardSummary()
        {
            var data = _studentService.GetDashboardData();
            return Ok(data);
        }

        // GET: api/predictionsapi/students
        [HttpGet("students")]
        public IActionResult GetStudents([FromQuery] string? search, [FromQuery] RiskLevel? riskFilter)
        {
            var students = _studentService.GetAllStudents(search, riskFilter);
            return Ok(students);
        }

        // GET: api/predictionsapi/students/1
        [HttpGet("students/{id}")]
        public IActionResult GetStudentDetail(int id)
        {
            var detail = _studentService.GetStudentRiskDetail(id);
            if (detail == null) return NotFound(new { message = $"Không tìm thấy sinh viên ID {id}" });
            return Ok(detail);
        }
    }
}
