import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Select, Spin, Empty, 
  Button, Divider, Tabs, Tag, Space, message
} from 'antd';
import { 
  PlayCircleOutlined,
  StopOutlined,
  SyncOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const API_URL = 'http://localhost:8000/api';

const WeeklyReportPage = () => {
  const [availableWeeks, setAvailableWeeks] = useState([]);
  const [selectedWeek, setSelectedWeek] = useState(0); // Default to current week
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);

  // Get available weekly reports
  const fetchAvailableWeeks = async () => {
    try {
      const response = await axios.get(`${API_URL}/analysis/available_weeks`);
      setAvailableWeeks(response.data.weekly_reports || []);
    } catch (error) {
      console.error('Failed to get available weekly reports', error);
    }
  };

  // Check analysis status
  const checkAnalysisStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/analysis/weekly_analysis_status`);
      setAnalysisRunning(response.data.is_running);
      
      // If analysis is complete, refresh reports and list
      if (!response.data.is_running && statusCheckInterval) {
        clearInterval(statusCheckInterval);
        setStatusCheckInterval(null);
        await fetchAvailableWeeks();
        await fetchWeeklyReport(selectedWeek);
      }
    } catch (error) {
      console.error('Failed to get analysis status', error);
    }
  };

  // Start weekly analysis
  const startAnalysis = async () => {
    try {
      const response = await axios.post(`${API_URL}/analysis/start_weekly_analysis?weeks_ago=${selectedWeek}`);
      
      if (response.data.success) {
        message.success('Weekly analysis started');
        setAnalysisRunning(true);
        
        // Set interval to check status
        const interval = setInterval(checkAnalysisStatus, 3000);
        setStatusCheckInterval(interval);
      } else {
        message.error(response.data.message || 'Failed to start analysis');
      }
    } catch (error) {
      message.error('Failed to start analysis: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Stop weekly analysis
  const stopAnalysis = async () => {
    try {
      const response = await axios.post(`${API_URL}/analysis/stop_weekly_analysis`);
      
      if (response.data.success) {
        message.success('Weekly analysis stopped');
        setAnalysisRunning(false);
        
        if (statusCheckInterval) {
          clearInterval(statusCheckInterval);
          setStatusCheckInterval(null);
        }
      } else {
        message.error(response.data.message || 'Failed to stop analysis');
      }
    } catch (error) {
      message.error('Failed to stop analysis: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Get weekly report data
  const fetchWeeklyReport = async (weeksAgo) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/analysis/weekly_report?weeks_ago=${weeksAgo}`);
      setReportData(response.data);
    } catch (error) {
      console.error('Failed to get weekly report data', error);
    } finally {
      setLoading(false);
    }
  };

  // Get available weekly reports and analysis status when component mounts
  useEffect(() => {
    fetchAvailableWeeks();
    checkAnalysisStatus();
    
    // Clear interval when component unmounts
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  // Get report when selected week changes
  useEffect(() => {
    fetchWeeklyReport(selectedWeek);
  }, [selectedWeek]);

  // Render report content
  const renderReportContent = () => {
    if (loading || analysisRunning) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p>{analysisRunning ? 'Generating weekly report...' : 'Loading report data...'}</p>
        </div>
      );
    }

    if (!reportData) {
      return <Empty description="No weekly report data available" />;
    }

    return (
      <div className="report-container markdown-content">
        <ReactMarkdown>
          {reportData.report_content}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div>
      <Title level={2}>Weekly Analysis</Title>
      
      <Card className="status-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Text strong>Select Week:</Text>
            <Select
              style={{ width: 200, marginLeft: 16 }}
              value={selectedWeek}
              onChange={setSelectedWeek}
              disabled={loading || analysisRunning}
            >
              <Option value={0}>Current Week</Option>
              <Option value={1}>Last Week</Option>
              <Option value={2}>Two Weeks Ago</Option>
              <Option value={3}>Three Weeks Ago</Option>
              <Option value={4}>Four Weeks Ago</Option>
            </Select>
          </div>
          
          <Space>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />} 
              onClick={startAnalysis}
              disabled={analysisRunning}
            >
              Start Analysis
            </Button>
            <Button 
              danger 
              icon={<StopOutlined />} 
              onClick={stopAnalysis}
              disabled={!analysisRunning}
            >
              Stop Analysis
            </Button>
            {analysisRunning && (
              <Text type="warning">
                <SyncOutlined spin /> Analysis in progress...
              </Text>
            )}
          </Space>
        </div>
        
        {reportData && (
          <div style={{ marginTop: 16 }}>
            <Tag color="blue">
              {reportData.start_date} to {reportData.end_date}
            </Tag>
          </div>
        )}
      </Card>
      
      <Card title="Weekly Report Content" className="status-card">
        {renderReportContent()}
      </Card>
      
      {availableWeeks.length > 0 && (
        <Card title="Historical Weekly Reports" className="status-card">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {availableWeeks.map((week, index) => (
              <Tag
                key={index}
                color="blue"
                style={{ cursor: 'pointer', margin: '0 8px 8px 0' }}
                onClick={() => {
                  // Find corresponding week number
                  const targetWeekStart = new Date(week.start_date);
                  const now = new Date();
                  const daysDiff = Math.floor((now - targetWeekStart) / (1000 * 60 * 60 * 24));
                  const weeksAgo = Math.floor(daysDiff / 7);
                  setSelectedWeek(weeksAgo > 4 ? 4 : weeksAgo);
                }}
              >
                {week.start_date} to {week.end_date}
              </Tag>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default WeeklyReportPage; 