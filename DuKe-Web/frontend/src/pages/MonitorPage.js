import React, { useState, useEffect } from 'react';
import { 
  Row, Col, Card, Button, Form, Input, 
  Tag, Space, Typography, Badge, Divider, Alert, 
  notification, Spin, Select 
} from 'antd';
import { PlusOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;
const { TextArea } = Input;
const API_URL = 'http://localhost:8000/api';

const MonitorPage = () => {
  const [form] = Form.useForm();
  const [monitorStatus, setMonitorStatus] = useState({ is_running: false });
  const [inputWhiteList, setInputWhiteList] = useState('');
  const [whiteList, setWhiteList] = useState([]);
  const [inputBlackList, setInputBlackList] = useState('');
  const [blackList, setBlackList] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingStatus, setFetchingStatus] = useState(false);

  // Fetch current monitoring status
  const fetchStatus = async () => {
    try {
      setFetchingStatus(true);
      const response = await axios.get(`${API_URL}/monitor/status`);
      setMonitorStatus(response.data);
      
      // If running, update the form
      if (response.data.is_running) {
        form.setFieldsValue({
          workGoal: response.data.work_goal || '',
        });
        setWhiteList(response.data.white_list || []);
        setBlackList(response.data.black_list || []);
      }
    } catch (error) {
      console.error('Failed to fetch monitoring status', error);
      notification.error({
        message: 'Failed to fetch monitoring status',
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setFetchingStatus(false);
    }
  };

  // Fetch recent logs
  const fetchRecentLogs = async () => {
    try {
      const response = await axios.get(`${API_URL}/monitor/recent_logs`);
      setRecentLogs(response.data.logs || []);
    } catch (error) {
      console.error('Failed to fetch recent logs', error);
    }
  };

  // Fetch status when component mounts
  useEffect(() => {
    fetchStatus();
    fetchRecentLogs();
    
    // Refresh status and logs periodically
    const intervalId = setInterval(() => {
      if (!loading) {
        fetchStatus();
        fetchRecentLogs();
      }
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [loading]);

  // Start monitoring
  const startMonitoring = async (values) => {
    try {
      setLoading(true);
      await axios.post(`${API_URL}/monitor/start`, {
        work_goal: values.workGoal,
        white_list: whiteList,
        black_list: blackList,
      });
      
      notification.success({
        message: 'Started Successfully',
        description: 'Focus monitoring has started',
      });
      
      await fetchStatus();
      await fetchRecentLogs();
    } catch (error) {
      console.error('Failed to start monitoring', error);
      notification.error({
        message: 'Start Failed',
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  // Stop monitoring
  const stopMonitoring = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_URL}/monitor/stop`);
      
      notification.success({
        message: 'Stopped Successfully',
        description: 'Focus monitoring has stopped',
      });
      
      await fetchStatus();
    } catch (error) {
      console.error('Failed to stop monitoring', error);
      notification.error({
        message: 'Stop Failed',
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  // Add whitelist application
  const addWhiteListItem = () => {
    if (inputWhiteList && !whiteList.includes(inputWhiteList)) {
      setWhiteList([...whiteList, inputWhiteList]);
      setInputWhiteList('');
    }
  };

  // Add blacklist application
  const addBlackListItem = () => {
    if (inputBlackList && !blackList.includes(inputBlackList)) {
      setBlackList([...blackList, inputBlackList]);
      setInputBlackList('');
    }
  };

  // Render monitoring status
  const renderStatus = () => {
    if (fetchingStatus) {
      return <Spin />;
    }

    return (
      <Badge
        status={monitorStatus.is_running ? 'success' : 'default'}
        text={
          <Text style={{ fontSize: 16 }}>
            Monitoring Status: {monitorStatus.is_running ? 'Running' : 'Stopped'}
          </Text>
        }
      />
    );
  };

  return (
    <div>
      <Title level={2}>Focus Monitoring</Title>
      <Card className="status-card">
        <Row gutter={16} align="middle">
          <Col span={12}>
            {renderStatus()}
            {monitorStatus.is_running && (
              <div style={{ marginTop: 8 }}>
                <Text>Current Work Goal: {monitorStatus.work_goal}</Text>
              </div>
            )}
          </Col>
          <Col span={12} style={{ textAlign: 'right' }}>
            <Button
              type="primary"
              danger={monitorStatus.is_running}
              loading={loading}
              onClick={monitorStatus.is_running ? stopMonitoring : () => form.submit()}
            >
              {monitorStatus.is_running ? 'Stop Monitoring' : 'Start Monitoring'}
            </Button>
          </Col>
        </Row>
      </Card>

      {!monitorStatus.is_running && (
        <Card title="Monitoring Settings" className="status-card">
          <Form
            form={form}
            layout="vertical"
            onFinish={startMonitoring}
            className="settings-form"
          >
            <Form.Item
              name="workGoal"
              label="Work Goal"
              rules={[{ required: true, message: 'Please enter your work goal' }]}
            >
              <TextArea
                placeholder="Please enter your work goal, e.g.: writing reports, learning programming, etc."
                autoSize={{ minRows: 2, maxRows: 4 }}
              />
            </Form.Item>

            <Form.Item label="Work-related Applications (Whitelist)">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space wrap>
                  {whiteList.map((item, index) => (
                    <Tag
                      key={index}
                      closable
                      onClose={() => setWhiteList(whiteList.filter((_, i) => i !== index))}
                    >
                      {item}
                    </Tag>
                  ))}
                </Space>
                <Input
                  placeholder="Enter work-related applications, press Enter to add"
                  value={inputWhiteList}
                  onChange={(e) => setInputWhiteList(e.target.value)}
                  onPressEnter={addWhiteListItem}
                  suffix={
                    <Button type="text" icon={<PlusOutlined />} onClick={addWhiteListItem} />
                  }
                />
              </Space>
            </Form.Item>

            <Form.Item label="Distracting Applications (Blacklist)">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space wrap>
                  {blackList.map((item, index) => (
                    <Tag
                      key={index}
                      color="red"
                      closable
                      onClose={() => setBlackList(blackList.filter((_, i) => i !== index))}
                    >
                      {item}
                    </Tag>
                  ))}
                </Space>
                <Input
                  placeholder="Enter distracting applications, press Enter to add"
                  value={inputBlackList}
                  onChange={(e) => setInputBlackList(e.target.value)}
                  onPressEnter={addBlackListItem}
                  suffix={
                    <Button type="text" icon={<PlusOutlined />} onClick={addBlackListItem} />
                  }
                />
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )}

      <Card title="Recent Monitoring Records">
        {recentLogs.length > 0 ? (
          recentLogs.map((log, index) => {
            const isFocused = log.includes('"status": "1. Focused"');
            return (
              <div key={index} style={{ marginBottom: 16 }}>
                <Alert
                  type={isFocused ? 'success' : 'warning'}
                  message={
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        {isFocused ? (
                          <CheckCircleOutlined style={{ color: 'green', marginRight: 8 }} />
                        ) : (
                          <CloseCircleOutlined style={{ color: 'red', marginRight: 8 }} />
                        )}
                        <Text strong>{isFocused ? 'Focused' : 'Distracted'}</Text>
                      </div>
                      <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                        {log}
                      </pre>
                    </div>
                  }
                />
              </div>
            );
          })
        ) : (
          <Text>No monitoring records yet</Text>
        )}
      </Card>
    </div>
  );
};

export default MonitorPage; 