import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import { 
  AppstoreOutlined, 
  AreaChartOutlined, 
  FileTextOutlined, 
  BarChartOutlined 
} from '@ant-design/icons';
import './App.css';

// Import page components
import MonitorPage from './pages/MonitorPage';
import FatiguePage from './pages/FatiguePage';
import DailyReportPage from './pages/DailyReportPage';
import WeeklyReportPage from './pages/WeeklyReportPage';

const { Header, Content, Footer, Sider } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState('monitor');
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Render the currently selected page
  const renderContent = () => {
    switch (currentPage) {
      case 'monitor':
        return <MonitorPage />;
      case 'fatigue':
        return <FatiguePage />;
      case 'daily':
        return <DailyReportPage />;
      case 'weekly':
        return <WeeklyReportPage />;
      default:
        return <MonitorPage />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div className="logo">
          {!collapsed && <h2 style={{ color: 'white', textAlign: 'center', margin: '16px 0' }}>DuKe</h2>}
          {collapsed && <h2 style={{ color: 'white', textAlign: 'center', margin: '16px 0' }}>D</h2>}
        </div>
        <Menu
          theme="dark"
          defaultSelectedKeys={['monitor']}
          mode="inline"
          onSelect={({ key }) => setCurrentPage(key)}
          items={[
            {
              key: 'monitor',
              icon: <AppstoreOutlined />,
              label: 'Real-time Monitoring',
            },
            {
              key: 'fatigue',
              icon: <AreaChartOutlined />,
              label: 'Fatigue Analysis',
            },
            {
              key: 'daily',
              icon: <FileTextOutlined />,
              label: 'Daily Analysis',
            },
            {
              key: 'weekly',
              icon: <BarChartOutlined />,
              label: 'Weekly Analysis',
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }} />
        <Content style={{ margin: '0 16px' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              marginTop: 16,
            }}
          >
            {renderContent()}
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          DuKe Focus Monitoring and Analysis System ©{new Date().getFullYear()} Created by DuKe Team
        </Footer>
      </Layout>
    </Layout>
  );
}

export default App; 