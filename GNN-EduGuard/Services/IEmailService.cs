using GNN_EduGuard.Models;

namespace GNN_EduGuard.Services
{
    public class BulkEmailResult
    {
        public int TotalTargets { get; set; }
        public int SentCount { get; set; }
        public int FailedCount { get; set; }
        public List<string> Errors { get; set; } = new();
    }

    public interface IEmailService
    {
        Task<BulkEmailResult> SendBulkWarningEmailsAsync(
            IEnumerable<Student> students,
            string? advisorNote = null);
    }
}
