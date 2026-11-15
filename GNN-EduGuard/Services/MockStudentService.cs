using System.Text;
using GNN_EduGuard.Models;
using GNN_EduGuard.Models.ViewModels;

namespace GNN_EduGuard.Services
{
    public class MockStudentService : IStudentService
    {
        private static readonly object _lock = new();
        private static readonly List<Student> _students = InitializeStudents();
        private static readonly List<InterventionLog> _interventionLogs = InitializeInterventions();

        private static List<Student> InitializeStudents()
        {
            return new List<Student>
            {
                new Student
                {
                    Id = 1,
                    StudentCode = "SV2380601",
                    FullName = "Nguyễn Văn An",
                    Email = "an.nguyen@edu.vn",
                    ClassName = "CNTT-K23A",
                    Gender = "Nam",
                    Age = 20,
                    GpaBefore = 1.85,
                    AttendedSessions = 5,
                    TotalSessions = 9,
                    TotalVleClicks = 82,
                    LateSubmissionRate = 0.65,
                    AssignmentAverageScore = 42.5,
                    RiskProbability = 0.90,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Vắng học 4/9 buổi (chuyên cần 56% < 80% quy định cấm thi) & Tương tác VLE thấp",
                    LastEvaluatedAt = DateTime.Now.AddHours(-2)
                },
                new Student
                {
                    Id = 2,
                    StudentCode = "SV2380602",
                    FullName = "Trần Thị Mai",
                    Email = "mai.tran@edu.vn",
                    ClassName = "CNTT-K23A",
                    Gender = "Nữ",
                    Age = 19,
                    GpaBefore = 2.10,
                    AttendedSessions = 6,
                    TotalSessions = 9,
                    TotalVleClicks = 145,
                    LateSubmissionRate = 0.40,
                    AssignmentAverageScore = 55.0,
                    RiskProbability = 0.78,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Vắng học 3/9 buổi (67% chuyên cần - Nguy cơ cấm thi) & Điểm bài tập dưới trung bình",
                    LastEvaluatedAt = DateTime.Now.AddHours(-5)
                },
                new Student
                {
                    Id = 3,
                    StudentCode = "SV2380603",
                    FullName = "Lê Hoàng Phúc",
                    Email = "phuc.le@edu.vn",
                    ClassName = "CNTT-K23B",
                    Gender = "Nam",
                    Age = 21,
                    GpaBefore = 2.45,
                    AttendedSessions = 8,
                    TotalSessions = 9,
                    TotalVleClicks = 210,
                    LateSubmissionRate = 0.25,
                    AssignmentAverageScore = 62.0,
                    RiskProbability = 0.54,
                    RiskLevel = RiskLevel.Moderate,
                    TopRiskFactor = "Đã vắng 1/9 buổi (89% chuyên cần, sát ngưỡng cấm thi) & Điểm giảm nhẹ",
                    LastEvaluatedAt = DateTime.Now.AddDays(-1)
                },
                new Student
                {
                    Id = 4,
                    StudentCode = "SV2380604",
                    FullName = "Phạm Quỳnh Chi",
                    Email = "chi.pham@edu.vn",
                    ClassName = "CNTT-K23B",
                    Gender = "Nữ",
                    Age = 20,
                    GpaBefore = 3.65,
                    AttendedSessions = 9,
                    TotalSessions = 9,
                    TotalVleClicks = 680,
                    LateSubmissionRate = 0.0,
                    AssignmentAverageScore = 91.5,
                    RiskProbability = 0.06,
                    RiskLevel = RiskLevel.Safe,
                    TopRiskFactor = "Điểm danh 9/9 buổi (100%) & Hoạt động tích cực toàn diện",
                    LastEvaluatedAt = DateTime.Now.AddHours(-1)
                },
                new Student
                {
                    Id = 5,
                    StudentCode = "SV2380605",
                    FullName = "Đỗ Minh Khang",
                    Email = "khang.do@edu.vn",
                    ClassName = "CNTT-K23A",
                    Gender = "Nam",
                    Age = 20,
                    GpaBefore = 3.20,
                    AttendedSessions = 9,
                    TotalSessions = 9,
                    TotalVleClicks = 490,
                    LateSubmissionRate = 0.05,
                    AssignmentAverageScore = 84.0,
                    RiskProbability = 0.14,
                    RiskLevel = RiskLevel.Safe,
                    TopRiskFactor = "Điểm danh 9/9 buổi (100%) & Tiến độ học tập ổn định",
                    LastEvaluatedAt = DateTime.Now.AddDays(-2)
                },
                new Student
                {
                    Id = 6,
                    StudentCode = "SV2380606",
                    FullName = "Võ Quốc Cường",
                    Email = "cuong.vo@edu.vn",
                    ClassName = "CNTT-K23C",
                    Gender = "Nam",
                    Age = 22,
                    GpaBefore = 1.95,
                    AttendedSessions = 6,
                    TotalSessions = 9,
                    TotalVleClicks = 110,
                    LateSubmissionRate = 0.50,
                    AssignmentAverageScore = 48.0,
                    RiskProbability = 0.82,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Vắng học 3/9 buổi (67% chuyên cần - Nguy cơ cấm thi) & Chưa xem bài giảng VLE",
                    LastEvaluatedAt = DateTime.Now.AddHours(-6)
                },
                new Student
                {
                    Id = 7,
                    StudentCode = "SV2380607",
                    FullName = "Bùi Thu Hà",
                    Email = "ha.bui@edu.vn",
                    ClassName = "CNTT-K23C",
                    Gender = "Nữ",
                    Age = 20,
                    GpaBefore = 2.60,
                    AttendedSessions = 8,
                    TotalSessions = 9,
                    TotalVleClicks = 260,
                    LateSubmissionRate = 0.20,
                    AssignmentAverageScore = 67.5,
                    RiskProbability = 0.42,
                    RiskLevel = RiskLevel.Moderate,
                    TopRiskFactor = "Điểm danh 8/9 buổi (89% - vắng 1 buổi) & Điểm kiểm tra giữa kỳ thấp hơn kỳ vọng",
                    LastEvaluatedAt = DateTime.Now.AddDays(-1)
                }
            };
        }

        private static List<InterventionLog> InitializeInterventions()
        {
            return new List<InterventionLog>
            {
                new InterventionLog
                {
                    Id = 1,
                    StudentId = 1,
                    AdvisorName = "CVHT. Nguyễn Minh Đức",
                    ActionType = "Cảnh báo Điểm danh & Nhắc nhở LMS",
                    Notes = "Đã liên hệ nhắc sinh viên Nguyễn Văn An về việc vắng 4/9 buổi học (56% < 80% chuyên cần) và hướng dẫn học bù Bài tập #2.",
                    CreatedAt = DateTime.Now.AddDays(-2)
                }
            };
        }

        public static RiskLevel ClassifyRisk(double probability)
        {
            if (probability >= 0.70) return RiskLevel.HighRisk;
            if (probability >= 0.40) return RiskLevel.Moderate;
            return RiskLevel.Safe;
        }

        public void SyncStudentPrediction(int id, double riskProb, string? topReason = null, int? attendedSessions = null, int? totalSessions = null)
        {
            lock (_lock)
            {
                var student = _students.FirstOrDefault(s => s.Id == id);
                if (student != null)
                {
                    if (totalSessions.HasValue && totalSessions.Value > 0)
                    {
                        student.TotalSessions = totalSessions.Value;
                    }
                    if (attendedSessions.HasValue)
                    {
                        student.AttendedSessions = Math.Clamp(attendedSessions.Value, 0, student.TotalSessions);
                    }
                    student.RiskProbability = riskProb;
                    student.RiskLevel = ClassifyRisk(riskProb);
                    if (!string.IsNullOrWhiteSpace(topReason))
                    {
                        student.TopRiskFactor = topReason;
                    }
                    student.LastEvaluatedAt = DateTime.Now;
                }
            }
        }

        public Task UpdateStudentAttendanceAsync(int studentId, int attendedSessions, int totalSessions = 9)
        {
            lock (_lock)
            {
                var student = _students.FirstOrDefault(s => s.Id == studentId);
                if (student != null)
                {
                    student.TotalSessions = Math.Max(1, totalSessions);
                    student.AttendedSessions = Math.Clamp(attendedSessions, 0, student.TotalSessions);

                    double attDelta = (0.85 - student.AttendanceRate) * 0.45 + (student.AbsentSessions >= 2 ? 0.14 : 0.0);
                    double baseScoreFactor = (100.0 - student.AssignmentAverageScore) / 140.0 + student.LateSubmissionRate * 0.30;
                    double newProb = Math.Clamp(baseScoreFactor + attDelta, 0.04, 0.98);
                    student.RiskProbability = Math.Round(newProb, 3);
                    student.RiskLevel = ClassifyRisk(student.RiskProbability);
                    student.TopRiskFactor = student.AbsentSessions >= 2
                        ? $"Vắng học {student.AbsentSessions}/{student.TotalSessions} buổi (chuyên cần {(int)(student.AttendanceRate * 100)}% < 80% quy định cấm thi)"
                        : $"Điểm danh {student.AttendedSessions}/{student.TotalSessions} buổi ({(int)(student.AttendanceRate * 100)}%)";
                    student.LastEvaluatedAt = DateTime.Now;
                }
            }
            return Task.CompletedTask;
        }

        public Task<DashboardViewModel> GetDashboardDataAsync()
        {
            lock (_lock)
            {
                var vm = new DashboardViewModel
                {
                    TotalStudents = _students.Count,
                    HighRiskCount = _students.Count(s => s.RiskLevel == RiskLevel.HighRisk),
                    ModerateRiskCount = _students.Count(s => s.RiskLevel == RiskLevel.Moderate),
                    SafeCount = _students.Count(s => s.RiskLevel == RiskLevel.Safe),
                    TopHighRiskStudents = _students
                        .Where(s => s.RiskLevel == RiskLevel.HighRisk)
                        .OrderByDescending(s => s.RiskProbability)
                        .ToList(),
                    RecentEvaluatedStudents = _students
                        .OrderByDescending(s => s.LastEvaluatedAt)
                        .Take(5)
                        .ToList()
                };
                return Task.FromResult(vm);
            }
        }

        public Task<List<Student>> GetAllStudentsAsync(string? search = null, RiskLevel? riskFilter = null)
        {
            lock (_lock)
            {
                var query = _students.AsQueryable();

                if (!string.IsNullOrWhiteSpace(search))
                {
                    var s = search.Trim().ToLower();
                    query = query.Where(x => x.FullName.ToLower().Contains(s) ||
                                             x.StudentCode.ToLower().Contains(s) ||
                                             x.ClassName.ToLower().Contains(s));
                }

                if (riskFilter.HasValue)
                {
                    query = query.Where(x => x.RiskLevel == riskFilter.Value);
                }

                return Task.FromResult(query.OrderByDescending(x => x.RiskProbability).ToList());
            }
        }

        public Task<Student?> GetStudentByIdAsync(int id)
        {
            lock (_lock)
            {
                return Task.FromResult(_students.FirstOrDefault(s => s.Id == id));
            }
        }

        public List<InterventionLog> GetInterventionsForStudent(int studentId)
        {
            lock (_lock)
            {
                return _interventionLogs
                    .Where(x => x.StudentId == studentId)
                    .OrderByDescending(x => x.CreatedAt)
                    .ToList();
            }
        }

        public Task AddInterventionLogAsync(int studentId, string advisorName, string actionType, string notes)
        {
            lock (_lock)
            {
                var nextId = _interventionLogs.Any() ? _interventionLogs.Max(x => x.Id) + 1 : 1;
                _interventionLogs.Add(new InterventionLog
                {
                    Id = nextId,
                    StudentId = studentId,
                    AdvisorName = string.IsNullOrWhiteSpace(advisorName) ? "Cố vấn Học tập" : advisorName.Trim(),
                    ActionType = string.IsNullOrWhiteSpace(actionType) ? "Tư vấn học tập" : actionType.Trim(),
                    Notes = notes.Trim(),
                    CreatedAt = DateTime.Now
                });
            }
            return Task.CompletedTask;
        }

        public async Task<byte[]> ExportStudentsCsvAsync(string? search = null, RiskLevel? riskFilter = null)
        {
            var students = await GetAllStudentsAsync(search, riskFilter);
            var sb = new StringBuilder();
            sb.AppendLine("Mã SV,Họ và tên,Email,Lớp,GPA Tích lũy,Điểm danh (9 Buổi/Kỳ),Tỷ lệ Chuyên cần (%),Clicks VLE,Tỷ lệ nộp trễ (%),Điểm TB Assignment,Xác suất nguy cơ (%),Mức độ cảnh báo,Nguyên nhân chính,Cập nhật lần cuối");

            foreach (var s in students)
            {
                var levelVi = s.RiskLevel switch
                {
                    RiskLevel.HighRisk => "Nguy cơ cao (>= 70%)",
                    RiskLevel.Moderate => "Cần theo dõi (40% - 69%)",
                    _ => "An toàn (< 40%)"
                };
                var safeReason = s.TopRiskFactor.Replace("\"", "\"\"");
                sb.AppendLine($"{s.StudentCode},\"{s.FullName}\",{s.Email},{s.ClassName},{s.GpaBefore:F2},{s.AttendedSessions}/{s.TotalSessions},{(int)(s.AttendanceRate * 100)},{s.TotalVleClicks},{(int)(s.LateSubmissionRate * 100)},{s.AssignmentAverageScore:F1},{(int)(s.RiskProbability * 100)},\"{levelVi}\",\"{safeReason}\",{s.LastEvaluatedAt:yyyy-MM-dd HH:mm}");
            }

            var preamble = Encoding.UTF8.GetPreamble();
            var body = Encoding.UTF8.GetBytes(sb.ToString());
            var result = new byte[preamble.Length + body.Length];
            Buffer.BlockCopy(preamble, 0, result, 0, preamble.Length);
            Buffer.BlockCopy(body, 0, result, preamble.Length, body.Length);
            return result;
        }

        public async Task<RiskPredictionDetail?> GetStudentRiskDetailAsync(int id)
        {
            var student = await GetStudentByIdAsync(id);
            if (student == null) return null;

            var detail = new RiskPredictionDetail
            {
                Student = student,
                InterventionHistory = GetInterventionsForStudent(id)
            };

            if (student.RiskLevel == RiskLevel.HighRisk)
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Tỷ lệ điểm danh chuyên cần trên lớp (Attendance - 9 buổi/kỳ)",
                        ImpactScore = +0.42,
                        Description = $"Điểm danh: {student.AttendedSessions}/{student.TotalSessions} buổi ({(int)(student.AttendanceRate * 100)}%, vắng {student.AbsentSessions} buổi - CẢNH BÁO CẤM THI | Chuẩn an toàn: 92%)",
                        IsNegativeImpact = true
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Lượt tương tác học liệu VLE (Clicks)",
                        ImpactScore = +0.35,
                        Description = $"Chỉ đạt {student.TotalVleClicks} clicks (thấp hơn 65% so với mức trung bình 380 clicks của lớp)",
                        IsNegativeImpact = true
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Tỷ lệ nộp bài trễ hạn (Late Submission)",
                        ImpactScore = +0.27,
                        Description = $"Tỷ lệ nộp muộn đạt {(int)(student.LateSubmissionRate * 100)}%, đặc biệt bài tập tuần 4 chưa nộp",
                        IsNegativeImpact = true
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Điểm trung bình Assignment",
                        ImpactScore = +0.22,
                        Description = $"Điểm hiện tại là {student.AssignmentAverageScore}/100, dưới ngưỡng an toàn 60 điểm",
                        IsNegativeImpact = true
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    $"Liên hệ xác minh lý do vắng học ({student.AbsentSessions}/{student.TotalSessions} buổi) và nhắc nhở quy định dự thi (tối thiểu 8/9 buổi có mặt).",
                    "Gửi thông báo khích lệ qua Email và LMS nhắc các mốc bài tập sắp tới.",
                    "Xếp lịch trao đổi 1-1 (15 phút) cùng giảng viên hoặc cố vấn học tập để tháo gỡ khó khăn.",
                    "Giới thiệu nhóm bạn học đồng hành (Peer-Tutoring) hỗ trợ ghi chép bài các buổi đã vắng."
                };
            }
            else if (student.RiskLevel == RiskLevel.Moderate)
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Tỷ lệ điểm danh chuyên cần trên lớp (Attendance - 9 buổi/kỳ)",
                        ImpactScore = +0.18,
                        Description = $"Điểm danh: {student.AttendedSessions}/{student.TotalSessions} buổi ({(int)(student.AttendanceRate * 100)}%, đã vắng {student.AbsentSessions} buổi - sát ngưỡng tối thiểu 80%)",
                        IsNegativeImpact = student.AbsentSessions >= 1
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Điểm số Assignment có xu hướng chững lại",
                        ImpactScore = +0.21,
                        Description = "Điểm giảm nhẹ ở 2 bài tập gần nhất so với giai đoạn đầu kỳ.",
                        IsNegativeImpact = true
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    "Nhắc nhở sinh viên đi học đầy đủ các buổi còn lại (không được vắng quá 1/9 buổi).",
                    "Khuyến khích sinh viên đặt câu hỏi trên diễn đàn môn học."
                };
            }
            else
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Tỷ lệ điểm danh chuyên cần trên lớp (Attendance - 9 buổi/kỳ)",
                        ImpactScore = -0.40,
                        Description = $"Điểm danh: {student.AttendedSessions}/{student.TotalSessions} buổi ({(int)(student.AttendanceRate * 100)}%, tham dự lớp học rất đầy đủ)",
                        IsNegativeImpact = false
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Tương tác VLE & Nộp bài đúng hạn",
                        ImpactScore = -0.38,
                        Description = $"Đạt {student.TotalVleClicks} clicks, xem đầy đủ tài liệu và nộp bài đúng hạn.",
                        IsNegativeImpact = false
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    "Sinh viên chuyên cần và học tập xuất sắc, có thể đề xuất làm trưởng nhóm Peer-Tutoring."
                };
            }

            return detail;
        }

        public async Task ReEvaluateStudentRiskAsync(int id)
        {
            var student = await GetStudentByIdAsync(id);
            if (student != null)
            {
                student.LastEvaluatedAt = DateTime.Now;
            }
        }
    }
}
