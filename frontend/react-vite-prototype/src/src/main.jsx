import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './styles.css'

const theme = {
  token: {
    fontFamily: "'Inter', -apple-system, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif",
    colorPrimary: '#1677FF',
    colorBgBase: '#FFFFFF',
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#FAFBFC',
    colorBorder: '#E5E7EB',
    colorBorderSecondary: '#F0F1F3',
    colorText: '#1A1A2E',
    colorTextSecondary: '#6B7280',
    colorTextTertiary: '#9CA3AF',
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,
    controlHeight: 36,
    fontSize: 14,
    boxShadow: '0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px -1px rgba(0,0,0,0.03)',
    boxShadowSecondary: '0 4px 12px -2px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04)',
  },
  components: {
    Card: {
      borderRadiusLG: 10,
    },
    Table: {
      borderRadius: 8,
    },
    Button: {
      borderRadius: 6,
    },
    Input: {
      borderRadius: 6,
    },
    Tag: {
      borderRadiusSM: 4,
    }
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider theme={theme} locale={zhCN}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>
)
