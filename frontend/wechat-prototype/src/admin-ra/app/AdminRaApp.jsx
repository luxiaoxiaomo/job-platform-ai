import React from 'react'
import { Admin, CustomRoutes, Layout, Menu, Resource } from 'react-admin'
import { createTheme, ThemeProvider } from '@mui/material'
import RuleIcon from '@mui/icons-material/Rule'
import ScienceIcon from '@mui/icons-material/Science'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import QueryStatsIcon from '@mui/icons-material/QueryStats'
import IntelligentIcon from '@mui/icons-material/PsychologyAlt'
import { Route } from 'react-router-dom'
import { authProvider } from './authProvider.js'
import { dataProvider } from './dataProvider.js'
import MatchAuditList from '../resources/match-audits/list.jsx'
import MatchQualityDashboard from '../resources/match-quality/dashboard.jsx'
import MatchRuleCompare from '../resources/match-rules/compare.jsx'
import MatchRuleEdit from '../resources/match-rules/edit.jsx'
import MatchRuleHistory from '../resources/match-rules/history.jsx'
import MatchRuleList from '../resources/match-rules/list.jsx'
import MatchRuleRelease from '../resources/match-rules/release.jsx'
import MatchRuleShow from '../resources/match-rules/show.jsx'
import RuleExperimentList from '../resources/rule-experiments/list.jsx'
import IntelligentStrategyForm from '../resources/intelligent-strategies/form.jsx'
import IntelligentStrategyList from '../resources/intelligent-strategies/list.jsx'
import IntelligentStrategyShow from '../resources/intelligent-strategies/show.jsx'

const theme = createTheme({
  palette: {
    primary: { main: '#07C160' },
    secondary: { main: '#10AEFF' },
    error: { main: '#FA5151' },
    warning: { main: '#FA9D3B' },
  },
  shape: { borderRadius: 8 },
})

const AppMenu = () => (
  <Menu>
    <Menu.DashboardItem />
    <Menu.ResourceItem name="match-rules" primaryText="Match Rules" leftIcon={<RuleIcon />} />
    <Menu.Item to="/admin-ra/match-audits" primaryText="Match Audits" leftIcon={<FactCheckIcon />} />
    <Menu.Item to="/admin-ra/match-quality" primaryText="Match Quality" leftIcon={<QueryStatsIcon />} />
    <Menu.Item to="/admin-ra/intelligent-matching/strategies" primaryText="Intelligent Matching" leftIcon={<IntelligentIcon />} />
    <Menu.Item to="/admin-ra/rule-experiments" primaryText="Rule AB Tests" leftIcon={<ScienceIcon />} />
  </Menu>
)

const AppLayout = (props) => <Layout {...props} menu={AppMenu} />

export default function AdminRaApp() {
  return (
    <ThemeProvider theme={theme}>
      <Admin
        basename="/admin-ra"
        dataProvider={dataProvider}
        authProvider={authProvider}
        layout={AppLayout}
        theme={theme}
        title="Rule Management Console"
        requireAuth
      >
        <Resource
          name="match-rules"
          icon={RuleIcon}
          list={MatchRuleList}
          show={MatchRuleShow}
          edit={MatchRuleEdit}
          options={{ label: 'Match Rules' }}
        />
        <CustomRoutes>
          <Route path="match-rules/:id/history" element={<MatchRuleHistory />} />
          <Route path="match-rules/:id/release" element={<MatchRuleRelease />} />
          <Route path="match-rules/:id/compare/:targetId" element={<MatchRuleCompare />} />
          <Route path="match-audits" element={<MatchAuditList />} />
          <Route path="match-quality" element={<MatchQualityDashboard />} />
          <Route path="intelligent-matching/strategies" element={<IntelligentStrategyList />} />
          <Route path="intelligent-matching/strategies/create" element={<IntelligentStrategyForm mode="create" />} />
          <Route path="intelligent-matching/strategies/:id" element={<IntelligentStrategyShow />} />
          <Route path="intelligent-matching/strategies/:id/edit" element={<IntelligentStrategyForm mode="edit" />} />
          <Route path="rule-experiments" element={<RuleExperimentList />} />
        </CustomRoutes>
      </Admin>
    </ThemeProvider>
  )
}
