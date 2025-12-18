import React, { useState } from 'react'
import { Layout, Menu, Typography, Space, Badge, Button, Tooltip } from 'antd'
import {
  SettingOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  GlobalOutlined
} from '@ant-design/icons'

import LandingPage from './components/LandingPage'
import ConfigPage from './pages/ConfigPage'
import TasksPage from './pages/TasksPage'
import ExecutionPage from './pages/ExecutionPage'
import ReportsPage from './pages/ReportsPage'
import { useLanguage } from './contexts/LanguageContext'

const { Header, Content, Sider } = Layout
const { Title, Text } = Typography

function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [currentPage, setCurrentPage] = useState('config')
  const { language, toggleLanguage, t } = useLanguage()

  // Show landing page as entry
  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />
  }

  const menuItems = [
    {
      key: 'config',
      icon: <SettingOutlined />,
      label: t('menu.config'),
    },
    {
      key: 'tasks',
      icon: <FileTextOutlined />,
      label: t('menu.tasks'),
    },
    {
      key: 'execution',
      icon: <PlayCircleOutlined />,
      label: t('menu.execution'),
    },
    {
      key: 'reports',
      icon: <FileSearchOutlined />,
      label: t('menu.reports'),
    },
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'config':
        return <ConfigPage />
      case 'tasks':
        return <TasksPage />
      case 'execution':
        return <ExecutionPage />
      case 'reports':
        return <ReportsPage />
      default:
        return <ConfigPage />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
      <Header style={{
        background: '#dc2626',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        height: 'auto',
        minHeight: '120px',
        position: 'relative',
        overflow: 'visible',
        zIndex: 10
      }}>
        {/* Language Switcher - Left side */}
        <div style={{ position: 'absolute', left: 32, top: '50%', transform: 'translateY(-50%)', zIndex: 20 }}>
          <Tooltip title={t('language.switchTo')}>
            <Button
              type="text"
              icon={<GlobalOutlined />}
              onClick={toggleLanguage}
              style={{
                color: 'rgba(255,255,255,0.9)',
                fontSize: '14px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                height: 'auto',
                background: 'rgba(255,255,255,0.15)',
                border: '1px solid rgba(255,255,255,0.25)',
                borderRadius: '16px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.25)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
              }}
            >
              {language === 'zh' ? 'EN' : '中文'}
            </Button>
          </Tooltip>
        </div>

        {/* Logo and Title - Center */}
        <Space
          size="middle"
          align="center"
          direction="vertical"
          style={{
            color: 'white',
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 2,
            textAlign: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', justifyContent: 'center' }}>
            <img
              src="/finsight-logo-v3.png"
              alt="FinSight Logo"
              style={{
                height: '80px',
                width: '80px',
                objectFit: 'contain',
                filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.3))'
              }}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23fff" rx="20"/><text x="50" y="60" text-anchor="middle" dominant-baseline="middle" font-size="50" fill="%23dc2626" font-weight="bold">F</text></svg>';
              }}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0px', alignItems: 'flex-start' }}>
              <Title level={2} style={{
                color: 'white',
                margin: 0,
                fontWeight: 800,
                letterSpacing: '2px',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                lineHeight: '1.1',
                fontFamily: language === 'zh' ? '"PingFang SC", sans-serif' : '"Inter", "Segoe UI", sans-serif'
              }}>
                {t('header.title')}
              </Title>
              <Text style={{
                fontSize: '14px',
                color: 'rgba(255,255,255,0.85)',
                fontWeight: 400,
                letterSpacing: '1px',
                display: 'block',
              }}>
                {t('header.subtitle')}
              </Text>
            </div>
          </div>
        </Space>

        {/* Badge - Right side */}
        <div style={{ position: 'absolute', right: 32, top: '50%', transform: 'translateY(-50%)' }}>
          <Badge
            count={t('common.underDevelopment')}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              fontWeight: '600',
              border: '1px solid rgba(255,255,255,0.3)',
              fontSize: '12px',
              padding: '0 8px'
            }}
          />
        </div>
      </Header>

      <Layout style={{ background: 'transparent' }}>
        <Sider
          width={240}
          style={{
            background: '#ffffff',
            boxShadow: '2px 0 8px rgba(0, 0, 0, 0.06)',
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <div style={{
            padding: '24px 16px',
            borderBottom: '1px solid #f0f0f0',
            background: '#fafafa'
          }}>
            <Space>
              <DashboardOutlined style={{ fontSize: '20px', color: '#dc2626' }} />
              <Text strong style={{ fontSize: '16px', color: '#dc2626' }}>
                {t('header.controlPanel')}
              </Text>
            </Space>
          </div>
          <Menu
            mode="inline"
            selectedKeys={[currentPage]}
            items={menuItems}
            onClick={({ key }) => setCurrentPage(key)}
            style={{
              height: 'calc(100% - 73px)',
              borderRight: 0,
              paddingTop: '8px',
              background: 'transparent'
            }}
            theme="light"
            className="custom-menu"
          />
        </Sider>

        <Layout style={{ padding: '24px', background: 'transparent' }}>
          <Content
            style={{
              background: '#ffffff',
              padding: 32,
              margin: 0,
              minHeight: 280,
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              border: '1px solid #f0f0f0'
            }}
          >
            {renderPage()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App
