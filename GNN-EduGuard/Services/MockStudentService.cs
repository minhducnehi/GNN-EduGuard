using GNN_EduGuard.Models;
using GNN_EduGuard.Models.ViewModels;

namespace GNN_EduGuard.Services
{
    public class MockStudentService : IStudentService
    {
        private readonly List<Student> _students;

        public MockStudentService()
        {
            _students = new List<Student>
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
                    TotalVleClicks = 82,
                    LateSubmissionRate = 0.65,
                    AssignmentAverageScore = 42.5,
                    RiskProbability = 0.88,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Tương tác VLE giảm 70% & Nộp muộn 3 bài tập liên tiếp",
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
                    TotalVleClicks = 145,
                    LateSubmissionRate = 0.40,
                    AssignmentAverageScore = 55.0,
                    RiskProbability = 0.76,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Điểm bài tập lập trình dưới trung bình (40/100)",
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
                    TotalVleClicks = 210,
                    LateSubmissionRate = 0.25,
                    AssignmentAverageScore = 62.0,
                    RiskProbability = 0.54,
                    RiskLevel = RiskLevel.Moderate,
                    TopRiskFactor = "Xu hướng điểm giảm dần từ tuần 3 đến tuần 6",
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
                    TotalVleClicks = 680,
                    LateSubmissionRate = 0.0,
                    AssignmentAverageScore = 91.5,
                    RiskProbability = 0.08,
                    RiskLevel = RiskLevel.Safe,
                    TopRiskFactor = "Hoạt động tích cực toàn diện",
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
                    TotalVleClicks = 490,
                    LateSubmissionRate = 0.05,
                    AssignmentAverageScore = 84.0,
                    RiskProbability = 0.15,
                    RiskLevel = RiskLevel.Safe,
                    TopRiskFactor = "Tiến độ học tập ổn định",
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
                    TotalVleClicks = 110,
                    LateSubmissionRate = 0.50,
                    AssignmentAverageScore = 48.0,
                    RiskProbability = 0.79,
                    RiskLevel = RiskLevel.HighRisk,
                    TopRiskFactor = "Chưa xem video bài giảng 2 tuần liên tiếp",
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
                    TotalVleClicks = 260,
                    LateSubmissionRate = 0.20,
                    AssignmentAverageScore = 67.5,
                    RiskProbability = 0.42,
                    RiskLevel = RiskLevel.Moderate,
                    TopRiskFactor = "Điểm kiểm tra giữa kỳ thấp hơn kỳ vọng",
                    LastEvaluatedAt = DateTime.Now.AddDays(-1)
                }
            };
        }

        public DashboardViewModel GetDashboardData()
        {
            return new DashboardViewModel
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
        }

        public List<Student> GetAllStudents(string? search = null, RiskLevel? riskFilter = null)
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

            return query.OrderByDescending(x => x.RiskProbability).ToList();
        }

        public Student? GetStudentById(int id)
        {
            return _students.FirstOrDefault(s => s.Id == id);
        }

        public RiskPredictionDetail? GetStudentRiskDetail(int id)
        {
            var student = GetStudentById(id);
            if (student == null) return null;

            var detail = new RiskPredictionDetail
            {
                Student = student
            };

            // Mô phỏng kết quả phân tích XAI (GNN Attention & SHAP values)
            if (student.RiskLevel == RiskLevel.HighRisk)
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Lượt tương tác học liệu VLE (Clicks)",
                        ImpactScore = +0.38,
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
                    },
                    new RiskExplanation
                    {
                        FeatureName = "GPA học kỳ trước",
                        ImpactScore = +0.15,
                        Description = $"GPA tích lũy {student.GpaBefore:F2} nằm trong nhóm cảnh báo học vụ",
                        IsNegativeImpact = true
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    "Gửi thông báo nhắc nhở tự động qua Email và LMS về các deadline sắp tới.",
                    "Xếp lịch cố vấn học tập 1-1 với giảng viên hướng dẫn môn học.",
                    "Giới thiệu nhóm học tập hỗ trợ (peer-tutoring) trong lớp.",
                    "Kiểm tra tình trạng truy cập tài nguyên VLE của sinh viên."
                };
            }
            else if (student.RiskLevel == RiskLevel.Moderate)
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Điểm số Assignment có xu hướng giảm",
                        ImpactScore = +0.21,
                        Description = "Điểm giảm liên tiếp ở 2 bài tập gần nhất so với giai đoạn đầu kỳ.",
                        IsNegativeImpact = true
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Tương tác VLE trung bình",
                        ImpactScore = -0.10,
                        Description = $"Có {student.TotalVleClicks} clicks, duy trì xem bài học tương đối đều đặn.",
                        IsNegativeImpact = false
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    "Khuyến khích sinh viên tham gia diễn đàn trao đổi câu hỏi môn học.",
                    "Theo dõi kết quả bài kiểm tra tiếp theo trong 2 tuần tới."
                };
            }
            else
            {
                detail.Explanations = new List<RiskExplanation>
                {
                    new RiskExplanation
                    {
                        FeatureName = "Tương tác VLE xuất sắc",
                        ImpactScore = -0.45,
                        Description = $"Đạt {student.TotalVleClicks} clicks, xem đầy đủ tài liệu và video bài giảng.",
                        IsNegativeImpact = false
                    },
                    new RiskExplanation
                    {
                        FeatureName = "Nộp bài đúng hạn 100%",
                        ImpactScore = -0.35,
                        Description = "Toàn bộ bài tập đều được nộp sớm trước deadline.",
                        IsNegativeImpact = false
                    }
                };

                detail.RecommendedActions = new List<string>
                {
                    "Sinh viên học tập xuất sắc, có thể đề xuất làm trợ giảng hoặc trưởng nhóm học tập."
                };
            }

            return detail;
        }

        public void ReEvaluateStudentRisk(int id)
        {
            var student = GetStudentById(id);
            if (student != null)
            {
                student.LastEvaluatedAt = DateTime.Now;
            }
        }
    }
}
