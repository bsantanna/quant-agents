import {Component, computed, effect, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute} from '@angular/router';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';
import {PersonalAgentService} from '../shared/services/personal-agent.service';
import {AuthService} from '../shared/services/auth.service';
import {SeoService} from '../shared';

@Component({
  selector: 'app-insights-profile',
  imports: [],
  templateUrl: './insights-profile.html',
  styleUrl: './insights-profile.scss',
})
export class InsightsProfile {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly agentProfileService = inject(InsightsAgentProfileService);
  private readonly personalAgentService = inject(PersonalAgentService);
  private readonly authService = inject(AuthService);

  readonly profile = signal<AgentProfile | null>(null);
  readonly configuredTypes = signal<ReadonlySet<string>>(new Set());

  readonly ctaLabel = computed(() => {
    const p = this.profile();
    return p && this.configuredTypes().has(p.type)
      ? 'Configure personal agent'
      : 'Create personal agent';
  });

  agentSlug(agent: AgentProfile): string {
    return agent.type.replaceAll('_', '-');
  }

  constructor() {
    const seo = inject(SeoService);
    effect(() => {
      const agent = this.profile();
      if (agent) {
        const bio = agent.bio?.[0] ?? '';
        seo.update({
          title: agent.name,
          description: `${agent.role}${bio ? ` — ${bio}` : ''}`,
          path: `/insights/profile/${this.agentSlug(agent)}`,
          eyebrow: 'Insights',
        });
      }
    });

    if (this.isBrowser) {
      const agentName = this.route.snapshot.paramMap.get('agentName');
      if (agentName) {
        this.agentProfileService.getAgentProfile(agentName)
          .subscribe(data => this.profile.set(data));
      }

      if (this.authService.isLoggedIn()) {
        this.personalAgentService.list()
          .subscribe(personal => {
            this.configuredTypes.set(new Set(personal.map(p => p.agent_type)));
          });
      }
    }
  }
}
