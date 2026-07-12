import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

// In-memory data store
let users = [
  { id: "student-1", name: "Rahul Sharma", email: "rahul@email.com", course: "D2D Engineering", status: "pending", risk: "low", date: "2026-01-10", type: "D2D" },
  { id: "student-2", name: "Priya Patel", email: "priya@email.com", course: "B.Tech AIML", status: "approved", risk: "low", date: "2026-01-09", type: "Regular" }
];

// Auth Routes
app.post('/api/auth/student/register', (req, res) => {
  console.log('Student registration attempt:', req.body);
  const newUser = {
    id: `student-${users.length + 1}`,
    name: req.body.fullName,
    email: req.body.email,
    mobile: req.body.mobile,
    role: 'student',
    course: "Pending Selection", // Default until they apply
    status: "submitted",
    risk: "low",
    date: new Date().toISOString().split('T')[0],
    type: "Regular", // Default, can be updated later
    targetCollege: null,
    preferences: []
  };
  users.unshift(newUser);
  res.json({ success: true, message: 'Student registration successful', user: newUser, token: 'dummy_token' });
});

app.post('/api/auth/student/login', (req, res) => {
  console.log('Student login attempt:', req.body);
  const user = users.find(u => u.email === req.body.email);
  if (user) {
    // In demo, we'll allow any password for registered emails, but the email must exist.
    res.json({ success: true, message: 'Student login successful', token: 'dummy_token', user });
  } else {
    res.status(401).json({ success: false, message: 'Invalid email or password. Please register first.' });
  }
});

app.post('/api/auth/official/register', (req, res) => {
  console.log('Official registration attempt:', req.body);
  res.json({ success: true, message: 'Official registration successful', user: { id: 1, name: 'Test Official', role: 'official' } });
});

app.post('/api/auth/official/login', (req, res) => {
  console.log('Official login attempt:', req.body);
  res.json({ success: true, message: 'Official login successful', token: 'dummy_token', user: { id: 1, name: 'Test Official', role: 'official' } });
});

// Official Routes - Get Applications
app.get('/api/officials/applications', (req, res) => {
  res.json({ success: true, applications: users });
});

// Student Routes
app.get('/api/students/status', (req, res) => {
  res.json({ success: true, status: 'pending', message: 'Application under review' });
});

app.get('/api/students/dashboard', (req, res) => {
  res.json({
    success: true,
    stats: {
      applicationStatus: "pending",
      documentsStatus: "In Progress",
      pendingActions: 1,
      notifications: 2,
      uploadedDocuments: 0,
      totalDocuments: 5
    },
    student: {
      id: "1",
      name: "Test Student",
      course: "Computer Engineering"
    }
  });
});

app.get('/api/students/d2d-dashboard', (req, res) => {
  res.json({
    success: true,
    d2dData: {
      diplomaDetails: {
        college: "Polytechnic College",
        stream: "Computer Engineering",
        passingYear: "2024"
      },
      documents: [],
      status: "pending",
      requiredDocuments: [
        { id: "1", name: "10th Marksheet", required: true },
        { id: "2", name: "12th Marksheet", required: true },
        { id: "d2", name: "6th Sem Marksheet", required: true },
        { id: "d4", name: "Diploma LC", required: true }
      ]
    }
  });
});

app.get('/api/students/documents/required', (req, res) => {
  res.json({
    success: true,
    documents: [
      { id: '1', name: '10th Marksheet', required: true, status: 'pending' },
      { id: '2', name: '12th Marksheet', required: true, status: 'pending' },
      { id: '3', name: 'Photo ID', required: true, status: 'pending' }
    ]
  });
});

app.post('/api/students/documents/upload', (req, res) => {
  // Simulate file upload
  res.json({
    success: true,
    message: 'Document uploaded successfully',
    document: { fileName: 'uploaded-file.pdf' }
  });
});

app.post('/api/students/documents/submit', (req, res) => {
  res.json({ success: true, message: 'Application submitted successfully' });
});

// Official Routes
app.get('/api/officials/applications/:id', (req, res) => {
  const user = users.find(u => u.id === req.params.id);
  if (user) {
    res.json({
      success: true,
      application: user
    });
  } else {
    res.status(404).json({ success: false, message: 'Application not found' });
  }
});

app.get('/api/officials/applications/:id/documents', (req, res) => {
  // In a real app, this would look up documents for the studentId
  res.json({
    success: true,
    documents: [
      { id: '1', name: 'SSC Marksheet', url: '/uploads/dummy.pdf', status: 'verified' },
      { id: '2', name: 'HSC Marksheet', url: '/uploads/dummy.pdf', status: 'pending' },
      { id: '3', name: 'Identity Proof', url: '/uploads/dummy.pdf', status: 'verified' }
    ]
  });
});

app.post('/api/students/preferences', (req, res) => {
  const { studentId, preferences, targetCollege } = req.body;
  console.log(`Updating preferences for student ${studentId}:`, { preferences, targetCollege });

  const user = users.find(u => u.id === studentId || u.email === studentId);
  if (user) {
    if (preferences) user.preferences = preferences;
    if (targetCollege) user.targetCollege = targetCollege;
    res.json({ success: true, message: 'Selection updated successfully' });
  } else {
    res.status(404).json({ success: false, message: 'User not found' });
  }
});

app.post('/api/officials/applications/:id/action', (req, res) => {
  console.log(`Action taken on application ${req.params.id}:`, req.body);
  const user = users.find(u => u.id === req.params.id);
  if (user) {
    user.status = req.body.action === 'approve' ? 'approved' : req.body.action === 'reject' ? 'rejected' : 'query';
    user.notes = req.body.notes;
  }
  res.json({ message: 'Action recorded successfully' });
});

// College Routes
app.get('/api/colleges', (req, res) => {
  res.json({ colleges: [] });
});

app.get('/api/colleges/:id', (req, res) => {
  res.json({ id: req.params.id, name: 'Test College' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

export default app;
