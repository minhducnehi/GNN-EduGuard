using System.Net.Http.Json;
using System.Text.Json;
using GNN_EduGuard.Models;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers.Api
{
    public class AgentChatRequestDto
    {
        public string Message { get; set; } = string.Empty;
    }

    [ApiController]
    [Authorize]
    [Route("api/[controller]")]
    public class PredictionsApiController : ControllerBase
    {
        private readonly IStudentService _studentService;
        private readonly IHttpClientFactory _httpClientFactory;

        public PredictionsApiController(IStudentService studentService, IHttpClientFactory httpClientFactory)
        {
            _studentService = studentService;
            _httpClientFactory = httpClientFactory;
        }

        // GET: api/predictionsapi/dashboard
        [HttpGet("dashboard")]
        [Authorize(Roles = "Admin,Advisor")]
        public async Task<IActionResult> GetDashboardSummary()
        {
            var data = await _studentService.GetDashboardDataAsync();
            return Ok(data);
        }

        // GET: api/predictionsapi/students
        [HttpGet("students")]
        [Authorize(Roles = "Admin,Advisor")]
        public async Task<IActionResult> GetStudents([FromQuery] string? search, [FromQuery] RiskLevel? riskFilter)
        {
            var students = await _studentService.GetAllStudentsAsync(search, riskFilter);
            return Ok(students);
        }

        // GET: api/predictionsapi/students/1
        [HttpGet("students/{id}")]
        public async Task<IActionResult> GetStudentDetail(int id)
        {
            var detail = await _studentService.GetStudentRiskDetailAsync(id);
            if (detail == null) return NotFound(new { message = $"Không tìm thấy sinh viên ID {id}" });
            return Ok(detail);
        }

        // POST: api/predictionsapi/consult/1
        [HttpPost("consult/{id}")]
        public async Task<IActionResult> ConsultStudentWithAgent(int id)
        {
            var student = await _studentService.GetStudentByIdAsync(id);
            var payload = student != null ? new
            {
                student_id = id,
                name = student.FullName,
                gpa = student.GpaBefore,
                attendance_rate = student.AttendanceRate,
                total_sessions = student.TotalSessions,
                submission_rate = $"{(int)((1.0 - student.LateSubmissionRate) * 100)}%"
            } : new { student_id = id, name = $"Sinh viên #{id}", gpa = 2.0, attendance_rate = 0.889, total_sessions = 9, submission_rate = "60%" };

            try
            {
                var client = _httpClientFactory.CreateClient("AiEngine");
                var resp = await client.PostAsJsonAsync($"/api/agent/consult/{id}", payload);
                resp.EnsureSuccessStatusCode();
                var json = await resp.Content.ReadFromJsonAsync<JsonElement>();
                return Ok(json);
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { error = "Không thể kết nối tới Local AI Agent (:8000)", details = ex.Message });
            }
        }

        // POST: api/predictionsapi/chat
        [HttpPost("chat")]
        public async Task<IActionResult> ChatWithAgent([FromBody] AgentChatRequestDto req)
        {
            try
            {
                var client = _httpClientFactory.CreateClient("AiEngine");
                var resp = await client.PostAsJsonAsync("/api/agent/chat", new { message = req.Message });
                resp.EnsureSuccessStatusCode();
                var json = await resp.Content.ReadFromJsonAsync<JsonElement>();
                return Ok(json);
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { error = "Không thể kết nối tới Local AI Agent (:8000)", details = ex.Message });
            }
        }
    }
}
