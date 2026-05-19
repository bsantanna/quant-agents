import { Routes } from '@angular/router';
import {MarketsStocksDashboard} from './page-markets-stocks-dashboard';
import {PageTerms} from './page-terms';
import {MarketsNewsRelated} from './page-markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison';
import {MarketsNewsItem} from './page-markets-news-item';
import {MarketsStocks} from './page-markets-stocks';
import {MarketsNews} from './page-markets-news';
import {MarketsProfile} from './page-markets-profile/markets-profile';
import {InsightsAgents} from './page-insights-agents/insights-agents';
import {InsightsAgentsPersonal} from './page-insights-personal/insights-agents-personal';
import {InsightsProfile} from './page-insights-profile/insights-profile';
import {InsightsNews} from './page-insights-news/insights-news';
import {InsightsNewsItem} from './page-insights-news-item/insights-news-item';
import {InsightsPreview} from './page-insights-preview/insights-preview';
import {InsightsFinance} from './page-insights-finance/insights-finance';
import {AuthCallback} from './page-auth-callback';
import {PageSignup} from './page-signup';
import {AccountProfile} from './page-account-profile/account-profile';
import {authGuard} from './shared/guards/auth.guard';
import {Privacy} from './page-privacy/privacy';
import {McpClientsClaude} from './page-mcp-clients-claude/mcp-clients-claude';
import {McpClientsHowTo} from './page-mcp-clients-how-to/mcp-clients-how-to';
import {McpClientsHermes} from './page-mcp-clients-hermes/mcp-clients-hermes';
import {ProductFeatures} from './page-product-features/product-features';
import {ProductPricing} from './page-product-pricing/product-pricing';
import {PageLanding} from './page-landing';

export const routes: Routes = [
  {
    title: 'Financial Intelligence for AI Agents & Assistants',
    path: '',
    pathMatch: 'full',
    component: PageLanding
  },
  {
    title: 'Account',
    path: 'account',
    children: [
      {
        title: 'Profile',
        path: 'profile',
        component: AccountProfile,
        canActivate: [authGuard]
      }
    ]
  },
  {
    title: 'Product',
    path: 'product',
    children: [
      {
        title: 'Features',
        path: 'features',
        component: ProductFeatures,
      },
      {
        title: 'Pricing',
        path: 'pricing',
        component: ProductPricing
      }
    ]
  },
  {
    title: 'MCP Clients',
    path: 'mcp-clients',
    children: [
      {
        title: 'Overview',
        path: 'how-to',
        component: McpClientsHowTo
      },
      {
        title: 'Claude',
        path: 'claude',
        component: McpClientsClaude
      },
      {
        title: 'Hermes Agent',
        path: 'hermes',
        component: McpClientsHermes
      }
    ]
  },
  {
    title: 'Insights',
    path: 'insights',
    children: [
      {
        title: 'Quaks Agents',
        path: 'agents',
        component: InsightsAgents
      },
      {
        title: 'Configure Agent',
        path: 'agents/personal/:agentSlug',
        component: InsightsAgentsPersonal
      },
      {
        title: 'Agent Profile',
        path: 'profile/:agentName',
        component: InsightsProfile
      },
      {
        title: 'News Insights',
        path: 'news',
        component: InsightsNews
      },
      {
        title: 'News Insights',
        path: 'news/item/:indexName/:newsItemId',
        component: InsightsNewsItem
      },
      {
        title: 'Content Preview',
        path: 'preview/:docId',
        component: InsightsPreview
      },
      {
        title: 'Financial Insights',
        path: 'financial',
        component: InsightsFinance
      },
      {
        title: 'Financial Insights',
        path: 'financial/item/:indexName/:newsItemId',
        component: InsightsNewsItem
      }
    ]
  },
  {
    title: 'Markets',
    path: 'markets',
    children: [
      {
        title: 'Performance',
        path: 'performance',
        component: MarketsPerformanceComparison
      },
      {
        title: 'News',
        path: 'news',
        component: MarketsNews
      },
      {
        title: 'Article',
        path: 'news/item/:indexName/:newsItemId',
        component: MarketsNewsItem
      },
      {
        title: 'Feed',
        path: 'news/related/:keyTicker',
        component: MarketsNewsRelated
      },
      {
        title: 'Stocks',
        path: 'stocks',
        component: MarketsStocks
      },
      {
        title: 'Stocks Dashboard',
        path: 'stocks/:keyTicker',
        component: MarketsStocksDashboard
      },
      {
        title: 'Company Profile',
        path: 'profile/:keyTicker',
        component: MarketsProfile
      }
    ]
  },
  {
    title: 'Terms of Service',
    path: 'terms',
    component: PageTerms
  },
  {
    title: 'Privacy Policy',
    path: 'privacy',
    component: Privacy
  },
  {
    title: 'Sign In',
    path: 'auth/callback',
    component: AuthCallback
  },
  {
    title: 'Sign Up',
    path: 'signup',
    component: PageSignup
  },
  { path: '**', redirectTo: '' }
];
