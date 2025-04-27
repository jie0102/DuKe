import React, { useState, useEffect } from 'react';
import { Pie } from '@ant-design/plots';
import { 
  Card, Typography, DatePicker, Spin, Empty, 
  Row, Col, Statistic, Divider, List, 
  Progress, Descriptions, Tag,
  Button, message, Space
} from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  PlayCircleOutlined,
  StopOutlined,
  SyncOutlined
} from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;
const API_URL = 'http://localhost:8000/api';

const DailyReportPage = () => {
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(moment());
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);

  // Get available dates
  const fetchAvailableDates = async () => {
    try {
      const response = await axios.get(`${API_URL}/analysis/available_dates`);
      setAvailableDates([
        ...new Set([
          ...(response.data.log_dates || []),
          ...(response.data.report_dates || [])
        ])
      ]);
    } catch (error) {
      console.error('Failed to get available dates', error);
    }
  };

  // Check analysis status
  const checkAnalysisStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/analysis/analysis_status`);
      setAnalysisRunning(response.data.is_running);
      
      // If analysis is complete, refresh dates and report
      if (!response.data.is_running && statusCheckInterval) {
        clearInterval(statusCheckInterval);
        setStatusCheckInterval(null);
        await fetchAvailableDates();
        await fetchDailyReport(selectedDate);
      }
    } catch (error) {
      console.error('Failed to get analysis status', error);
    }
  };

  // Start daily analysis
  const startAnalysis = async () => {
    try {
      const dateStr = selectedDate.format('YYYY-MM-DD');
      const response = await axios.post(`${API_URL}/analysis/start_daily_analysis?date=${dateStr}`);
      
      if (response.data.success) {
        message.success('Daily analysis started');
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

  // Stop daily analysis
  const stopAnalysis = async () => {
    try {
      const response = await axios.post(`${API_URL}/analysis/stop_daily_analysis`);
      
      if (response.data.success) {
        message.success('Daily analysis stopped');
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

  // Get report for specified date
  const fetchDailyReport = async (date) => {
    try {
      setLoading(true);
      const dateStr = date.format('YYYY-MM-DD');
      const response = await axios.get(`${API_URL}/analysis/daily_report?date=${dateStr}`);
      setReportData(response.data);
    } catch (error) {
      console.error('Failed to get daily report', error);
    } finally {
      setLoading(false);
    }
  };

  // Get available dates and analysis status when component mounts
  useEffect(() => {
    fetchAvailableDates();
    checkAnalysisStatus();
    
    // Clear interval when component unmounts
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  // Get report when date is selected
  useEffect(() => {
    if (selectedDate) {
      fetchDailyReport(selectedDate);
    }
  }, [selectedDate]);

  // Check if date is selectable
  const disabledDate = (current) => {
    if (availableDates.length === 0) return false;
    
    // Only allow selection of available dates
    const dateStr = current.format('YYYY-MM-DD');
    return !availableDates.includes(dateStr);
  };

  // Render pie chart data - commented out because Pie component is missing
  /*
  const renderPieChart = () => {
    if (!reportData) return null;
    
    const data = [
      { type: '专注', value: reportData.focus_count },
      { type: '分心', value: reportData.distraction_count }
    ];
    
    return (
      <Pie
        data={data}
        angleField="value"
        colorField="type"
        radius={0.8}
        label={{
          type: 'outer',
          content: '{name} {percentage}'
        }}
        interactions={[
          { type: 'pie-legend-active' },
          { type: 'element-active' }
        ]}
      />
    );
  };
  */

  // Render distraction reasons
  const renderDistractionReasons = () => {
    if (!reportData || Object.keys(reportData.distraction_reasons).length === 0) {
      return <Empty description="No distraction reason data" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
    }
    
    const reasonItems = Object.entries(reportData.distraction_reasons).map(([reason, count]) => ({
      reason,
      count
    })).sort((a, b) => b.count - a.count);
    
    return (
      <List
        itemLayout="horizontal"
        dataSource={reasonItems}
        renderItem={item => (
          <List.Item>
            <List.Item.Meta
              avatar={<CloseCircleOutlined style={{ color: 'red', fontSize: 18 }} />}
              title={item.reason}
              description={`Occurred ${item.count} times`}
            />
            <Progress 
              percent={item.count / reportData.distraction_count * 100} 
              size="small" 
              strokeColor="#ff4d4f"
              style={{ width: 100 }}
            />
          </List.Item>
        )}
      />
    );
  };

  // Render time period analysis
  const renderTimeAnalysis = () => {
    if (!reportData || !reportData.time_analysis) return null;
    
    const { time_analysis } = reportData;
    
    return (
      <Descriptions column={1} bordered>
        <Descriptions.Item label="High Focus Periods">
          {time_analysis.high_focus_periods || 'No data'}
        </Descriptions.Item>
        <Descriptions.Item label="High Distraction Periods">
          {time_analysis.high_distraction_periods || 'No data'}
        </Descriptions.Item>
        <Descriptions.Item label="High Focus Hours">
          {time_analysis.high_focus_hours || 'No data'}
        </Descriptions.Item>
        <Descriptions.Item label="High Distraction Hours">
          {time_analysis.high_distraction_hours || 'No data'}
        </Descriptions.Item>
      </Descriptions>
    );
  };

  return (
    <div>
      <Title level={2}>Daily Analysis</Title>
      
      <Card className="status-card">
        <Row gutter={16} align="middle">
          <Col span={12}>
            <Text strong>Select Date:</Text>
            <DatePicker
              style={{ marginLeft: 16 }}
              value={selectedDate}
              onChange={setSelectedDate}
              disabledDate={disabledDate}
              allowClear={false}
            />
          </Col>
          <Col span={12}>
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
          </Col>
        </Row>
      </Card>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p>Loading daily report data...</p>
        </div>
      ) : reportData ? (
        <>
          <Card title={`Focus Status Statistics (${reportData.date})`} className="status-card">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Focus Records"
                  value={reportData.focus_count}
                  suffix="times"
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Distraction Records"
                  value={reportData.distraction_count}
                  suffix="times"
                  valueStyle={{ color: '#f5222d' }}
                  prefix={<CloseCircleOutlined />}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Distraction Rate"
                  value={(reportData.distraction_ratio * 100).toFixed(1)}
                  suffix="%"
                  valueStyle={{ 
                    color: reportData.distraction_ratio > 0.5 ? '#f5222d' : 
                           reportData.distraction_ratio > 0.3 ? '#fa8c16' : '#52c41a' 
                  }}
                />
              </Col>
            </Row>
          </Card>
          
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Distraction Reason Analysis" className="status-card">
                {renderDistractionReasons()}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Time Period Analysis" className="status-card">
                {renderTimeAnalysis()}
              </Card>
            </Col>
          </Row>
          
          <Card title="Complete Daily Report" className="status-card">
            <div className="report-container markdown-content">
              <ReactMarkdown>
                {reportData.report_content}
              </ReactMarkdown>
            </div>
          </Card>
        </>
      ) : (
        <Empty description="Please select a date to view the report" />
      )}
    </div>
  );
};

export default DailyReportPage; 