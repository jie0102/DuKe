import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Statistic, Row, Col, Tag, Spin, 
  Button, Progress, Divider, Alert, Empty 
} from 'antd';
import { 
  AreaChartOutlined, LikeOutlined, 
  InfoCircleOutlined, WarningOutlined, StopOutlined 
} from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;
const API_URL = 'http://localhost:8000/api';

// Get color based on fatigue level
const getLevelColor = (level, color) => {
  if (level.includes('Good')) return '#52c41a';
  if (level.includes('Mild')) return '#faad14';
  if (level.includes('Moderate')) return '#fa8c16';
  if (level.includes('High')) return '#f5222d';
  
  if (color === 'Blue') return '#1890ff';
  if (color === 'Sky Blue ~ Orange') return '#faad14';
  if (color === 'Orange') return '#fa8c16';
  if (color === 'Red') return '#f5222d';
  
  return '#1890ff'; // Default color
};

// Get icon based on fatigue level
const getLevelIcon = (level) => {
  if (level.includes('Good')) return <LikeOutlined />;
  if (level.includes('Mild')) return <InfoCircleOutlined />;
  if (level.includes('Moderate')) return <WarningOutlined />;
  if (level.includes('High')) return <StopOutlined />;
  return <AreaChartOutlined />;
};

const FatiguePage = () => {
  const [currentFatigue, setCurrentFatigue] = useState(null);
  const [fatigueReport, setFatigueReport] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  // Get current fatigue data
  const fetchCurrentFatigue = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/fatigue/current`);
      setCurrentFatigue(response.data);
    } catch (error) {
      console.error('Failed to get fatigue data', error);
    } finally {
      setLoading(false);
    }
  };

  // Get historical fatigue data
  const fetchHistoricalData = async () => {
    try {
      const response = await axios.get(`${API_URL}/fatigue/historical`);
      setHistoricalData(response.data.historical_data || []);
    } catch (error) {
      console.error('Failed to get historical fatigue data', error);
    }
  };

  // Generate fatigue intervention report
  const generateFatigueReport = async () => {
    try {
      setReportLoading(true);
      const response = await axios.get(`${API_URL}/fatigue/report`);
      setFatigueReport(response.data);
    } catch (error) {
      console.error('Failed to generate fatigue report', error);
    } finally {
      setReportLoading(false);
    }
  };

  // Fetch data when component mounts
  useEffect(() => {
    fetchCurrentFatigue();
    fetchHistoricalData();
    
    // Refresh data periodically
    const intervalId = setInterval(() => {
      if (!loading && !reportLoading) {
        fetchCurrentFatigue();
        fetchHistoricalData();
      }
    }, 60000); // Refresh every 60 seconds
    
    return () => clearInterval(intervalId);
  }, [loading, reportLoading]);

  if (loading && !currentFatigue) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p>Loading fatigue data...</p>
      </div>
    );
  }

  if (!currentFatigue) {
    return (
      <Empty 
        description="No fatigue data available" 
        image={Empty.PRESENTED_IMAGE_SIMPLE} 
      />
    );
  }

  return (
    <div>
      <Title level={2}>Fatigue Analysis</Title>
      
      <Card className="status-card">
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="Current Fatigue Score"
              value={currentFatigue.score.toFixed(1)}
              suffix="%"
              valueStyle={{ color: getLevelColor(currentFatigue.level, currentFatigue.color) }}
              prefix={getLevelIcon(currentFatigue.level)}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color={getLevelColor(currentFatigue.level, currentFatigue.color)}>
                {currentFatigue.level}
              </Tag>
            </div>
          </Col>
          <Col span={8}>
            <Progress
              type="dashboard"
              percent={currentFatigue.score}
              strokeColor={getLevelColor(currentFatigue.level, currentFatigue.color)}
              format={(percent) => `${percent.toFixed(1)}%`}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Today's Records"
              value={currentFatigue.total_count}
              suffix={`times (Distracted ${currentFatigue.distraction_count} times)`}
            />
            <div style={{ marginTop: 8 }}>
              {currentFatigue.distraction_reasons.map((reason, index) => (
                <Tag key={index} color="volcano" style={{ marginBottom: 4 }}>
                  {reason}
                </Tag>
              ))}
            </div>
          </Col>
        </Row>
        
        <Divider />
        
        <Row>
          <Col span={24}>
            <Paragraph>
              <Text strong>Advice: </Text>
              <Text>{currentFatigue.advice}</Text>
            </Paragraph>
            {currentFatigue.intervene && !fatigueReport && (
              <Button 
                type="primary" 
                onClick={generateFatigueReport}
                loading={reportLoading}
              >
                Generate Intervention Report
              </Button>
            )}
          </Col>
        </Row>
      </Card>
      
      {fatigueReport && (
        <Card title="Fatigue Intervention Report" className="status-card">
          <div className="markdown-content">
            <ReactMarkdown>{fatigueReport.report}</ReactMarkdown>
          </div>
        </Card>
      )}
      
      <Card title="Historical Fatigue Trends" className="status-card">
        {historicalData.length > 0 ? (
          <div>
            {historicalData.map((item, index) => (
              <div key={index} style={{ marginBottom: 8 }}>
                <Row gutter={16} align="middle">
                  <Col span={4}>
                    <Text>{item.date}</Text>
                  </Col>
                  <Col span={16}>
                    <Progress
                      percent={item.score}
                      status={item.score === 0 ? 'normal' : undefined}
                      strokeColor={getLevelColor(item.level, item.color)}
                      size="small"
                    />
                  </Col>
                  <Col span={4}>
                    <Tag color={getLevelColor(item.level, item.color)}>
                      {item.level}
                    </Tag>
                  </Col>
                </Row>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No historical data" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>
    </div>
  );
};

export default FatiguePage; 