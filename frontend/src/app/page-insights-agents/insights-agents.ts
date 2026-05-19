import {Component, computed, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';
import {PersonalAgentService} from '../shared/services/personal-agent.service';
import {AuthService} from '../shared/services/auth.service';
import {SeoService} from '../shared';

@Component({
  selector: 'app-insights-agents',
  imports: [],
  templateUrl: './insights-agents.html',
  styleUrl: './insights-agents.scss',
})
export class InsightsAgents {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly agentProfileService = inject(InsightsAgentProfileService);
  private readonly personalAgentService = inject(PersonalAgentService);
  private readonly authService = inject(AuthService);

  readonly agents = signal<AgentProfile[]>([]);
  readonly configuredTypes = signal<ReadonlySet<string>>(new Set());

  readonly hasAnyConfigured = computed(() => this.configuredTypes().size > 0);

  constructor() {
    inject(SeoService).update({
      title: 'Quaks AI Agents',
      description: 'Browse and configure Quaks financial AI agents — news analyst, financial analyst, and more.',
      path: '/insights/agents',
    });
    if (this.isBrowser) {
      this.agentProfileService.getAllAgentProfiles()
        .subscribe(data => this.agents.set(data));

      if (this.authService.isLoggedIn()) {
        this.personalAgentService.list()
          .subscribe(personal => {
            this.configuredTypes.set(new Set(personal.map(p => p.agent_type)));
          });
      }
    }
  }

  agentSlug(agent: AgentProfile): string {
    return agent.type.replaceAll('_', '-');
  }

  hasPersonal(agent: AgentProfile): boolean {
    return this.configuredTypes().has(agent.type);
  }
}
