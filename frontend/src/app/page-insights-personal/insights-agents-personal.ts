import {computed, Component, effect, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';
import {forkJoin, Observable, of} from 'rxjs';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';
import {AuthService} from '../shared/services/auth.service';
import {FeedbackMessageService, SeoService} from '../shared';
import {LoginRequiredMessage} from '../shared/components/login-required-message/login-required-message';
import {ConfirmationDialog} from '../shared/components/confirmation-dialog/confirmation-dialog';
import {WizardButton} from '../shared/components/wizard-button/wizard-button';
import {WizardStepper} from '../shared/components/wizard-stepper/wizard-stepper';
import {PersonalAgentService} from '../shared/services/personal-agent.service';
import {PersonalAgent, PersonalAgentExpanded} from '../shared/models/personal-agent.models';

type WizardStep = 1 | 2 | 3 | 4;
type LoadState = 'loading' | 'ready' | 'error';

interface SettingDraft {
  key: string;
  value: string;
}

interface EditDraft {
  agent_name: string;
  agent_summary: string;
  settings: SettingDraft[];
}

interface SummaryRow {
  label: string;
  value: string;
}

@Component({
  selector: 'app-insights-agents-personal',
  imports: [FormsModule, LoginRequiredMessage, ConfirmationDialog, WizardButton, WizardStepper],
  templateUrl: './insights-agents-personal.html',
  styleUrl: './insights-agents-personal.scss',
})
export class InsightsAgentsPersonal {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly profileService = inject(InsightsAgentProfileService);
  private readonly agentService = inject(PersonalAgentService);
  private readonly authService = inject(AuthService);
  private readonly feedback = inject(FeedbackMessageService);

  readonly isLoggedIn = this.authService.isLoggedIn;
  readonly subscriptionTier = this.authService.subscriptionTier;

  readonly agentProfile = signal<AgentProfile | null>(null);
  readonly loadState = signal<LoadState>('loading');
  readonly currentStep = signal<WizardStep>(1);
  readonly existingAgent = signal<PersonalAgentExpanded | null>(null);
  readonly submitting = signal(false);
  readonly mode = signal<'create' | 'edit'>('create');
  readonly showResetConfirmation = signal(false);
  readonly showDeleteConfirmation = signal(false);

  readonly createName = signal('');
  readonly createNameError = signal<string | null>(null);
  readonly editDraft = signal<EditDraft>({agent_name: '', agent_summary: '', settings: []});

  private readonly allSteps: readonly {id: WizardStep; label: string}[] = [
    {id: 1, label: 'Create'},
    {id: 2, label: 'Configure'},
    {id: 3, label: 'Review'},
    {id: 4, label: 'Done'},
  ];

  readonly visibleSteps = computed(() => {
    const steps = this.mode() === 'edit'
      ? this.allSteps.filter(s => s.id !== 1)
      : this.allSteps;
    return steps.map((s, i) => ({id: s.id, displayId: i + 1, label: s.label}));
  });

  readonly reviewSummary = computed<SummaryRow[]>(() => {
    const draft = this.editDraft();
    const rows: SummaryRow[] = [
      {label: 'Description', value: draft.agent_summary},
    ];
    for (const setting of draft.settings) {
      rows.push({label: setting.key, value: setting.value});
    }
    return rows;
  });

  constructor() {
    const seo = inject(SeoService);
    effect(() => {
      const isEdit = this.mode() === 'edit';
      const profile = this.agentProfile();
      const name = profile?.name ?? (isEdit ? 'Configure Personal Agent' : 'Create Personal Agent');
      seo.update({
        title: name,
        description: isEdit
          ? `Configure your personal ${profile?.name ?? 'Quaks AI'} agent.`
          : `Create your personal ${profile?.name ?? 'Quaks AI'} agent.`,
        path: '/insights/agents/personal',
        eyebrow: 'Personal Agent',
      });
    });
    if (this.isBrowser) {
      this.initialize();
    }
  }

  private initialize(): void {
    const slug = this.route.snapshot.paramMap.get('agentSlug');
    if (!slug) {
      this.loadState.set('error');
      return;
    }
    forkJoin({
      profile: this.profileService.getAgentProfile(slug),
      agents: this.isLoggedIn() ? this.agentService.list() : of<PersonalAgent[]>([]),
    }).subscribe({
      next: ({profile, agents}) => {
        this.agentProfile.set(profile);
        const match = agents.find(a => a.agent_type === profile.type) ?? null;
        if (match) {
          this.loadExistingAgent(match.id);
        } else {
          this.loadState.set('ready');
        }
      },
      error: () => this.loadState.set('error'),
    });
  }

  private loadExistingAgent(agentId: string): void {
    this.agentService.getById(agentId).subscribe({
      next: expanded => {
        this.existingAgent.set(expanded);
        this.seedEditDraft(expanded);
        this.mode.set('edit');
        this.currentStep.set(2);
        this.loadState.set('ready');
      },
      error: () => this.loadState.set('error'),
    });
  }

  private seedEditDraft(expanded: PersonalAgentExpanded): void {
    this.editDraft.set({
      agent_name: expanded.agent_name,
      agent_summary: expanded.agent_summary ?? '',
      settings: (expanded.ag_settings ?? [])
        .slice()
        .sort((a, b) => a.setting_key.localeCompare(b.setting_key))
        .map(s => ({key: s.setting_key, value: s.setting_value})),
    });
  }

  private isValidAgentName(value: string): boolean {
    return /^[a-zA-Z0-9_-]+$/.test(value);
  }

  submitCreate(): void {
    const profile = this.agentProfile();
    if (!profile || this.submitting()) return;
    const name = this.createName().trim();
    if (!name) {
      this.createNameError.set('Name is required.');
      return;
    }
    if (!this.isValidAgentName(name)) {
      this.createNameError.set('Use letters, digits, hyphens, or underscores only.');
      return;
    }
    this.createNameError.set(null);
    this.submitting.set(true);
    this.agentService
      .create({agent_name: name, agent_type: profile.type})
      .subscribe({
        next: created => this.afterCreate(created.id),
        error: err => {
          this.submitting.set(false);
          this.feedback.update({
            message: err?.error?.detail ?? 'Failed to create agent. Please try again.',
            type: 'error',
            timeout: 3000,
          });
        },
      });
  }

  private afterCreate(agentId: string): void {
    this.agentService.getById(agentId).subscribe({
      next: expanded => {
        this.existingAgent.set(expanded);
        this.seedEditDraft(expanded);
        this.submitting.set(false);
        this.currentStep.set(2);
      },
      error: () => {
        this.submitting.set(false);
        this.feedback.update({
          message: 'Agent created, but failed to load its configuration.',
          type: 'error',
          timeout: 3000,
        });
      },
    });
  }

  updateSettingValue(key: string, value: string): void {
    this.editDraft.update(draft => ({
      ...draft,
      settings: draft.settings.map(s => (s.key === key ? {...s, value} : s)),
    }));
  }

  updateEditSummary(value: string): void {
    this.editDraft.update(draft => ({...draft, agent_summary: value}));
  }

  proceedFromEdit(): void {
    this.currentStep.set(3);
  }

  requestResetToFactory(): void {
    if (this.submitting()) return;
    this.showResetConfirmation.set(true);
  }

  confirmResetToFactory(): void {
    this.showResetConfirmation.set(false);
    this.resetToFactory();
  }

  cancelResetToFactory(): void {
    this.showResetConfirmation.set(false);
  }

  requestDeleteAgent(): void {
    if (this.submitting() || !this.existingAgent()) return;
    this.showDeleteConfirmation.set(true);
  }

  cancelDeleteAgent(): void {
    this.showDeleteConfirmation.set(false);
  }

  confirmDeleteAgent(): void {
    const agent = this.existingAgent();
    if (!agent || this.submitting()) return;
    this.showDeleteConfirmation.set(false);
    this.submitting.set(true);
    this.agentService.delete(agent.id).subscribe({
      next: () => {
        this.submitting.set(false);
        this.feedback.update({
          message: 'Agent deleted.',
          type: 'success',
          timeout: 3000,
        });
        this.router.navigate(['/insights/agents']);
      },
      error: (err: {error?: {detail?: string}}) => {
        this.submitting.set(false);
        this.feedback.update({
          message: err?.error?.detail ?? 'Failed to delete agent. Please try again.',
          type: 'error',
          timeout: 3000,
        });
      },
    });
  }

  resetToFactory(): void {
    const agent = this.existingAgent();
    if (!agent || this.submitting()) return;
    this.submitting.set(true);
    this.agentService.resetSettings(agent.id).subscribe({
      next: expanded => {
        this.existingAgent.set(expanded);
        this.seedEditDraft(expanded);
        this.submitting.set(false);
        this.feedback.update({
          message: 'Agent restored to factory defaults.',
          type: 'success',
          timeout: 3000,
        });
      },
      error: () => {
        this.submitting.set(false);
        this.feedback.update({
          message: 'Failed to reset agent. Please try again.',
          type: 'error',
          timeout: 3000,
        });
      },
    });
  }

  cancelConfirmation(): void {
    this.currentStep.set(2);
  }

  submitConfirmation(): void {
    const agent = this.existingAgent();
    const draft = this.editDraft();
    if (!agent || this.submitting()) return;
    this.submitting.set(true);

    const updateAgent$ = this.agentService.update({
      agent_id: agent.id,
      agent_name: draft.agent_name,
      agent_summary: draft.agent_summary,
      language_model_id: agent.language_model_id,
    });

    const originalSettings = new Map((agent.ag_settings ?? []).map(s => [s.setting_key, s.setting_value]));
    const changedSettings = draft.settings.filter(s => (originalSettings.get(s.key) ?? '') !== s.value);

    const calls: Observable<unknown>[] = [
      updateAgent$,
      ...changedSettings.map(s =>
        this.agentService.updateSetting({
          agent_id: agent.id,
          setting_key: s.key,
          setting_value: s.value,
        }),
      ),
    ];

    forkJoin(calls).subscribe({
      next: () => this.afterSave(agent.id),
      error: (err: {error?: {detail?: string}}) => {
        this.submitting.set(false);
        this.feedback.update({
          message: err?.error?.detail ?? 'Failed to save agent changes.',
          type: 'error',
          timeout: 3000,
        });
      },
    });
  }

  private afterSave(agentId: string): void {
    this.agentService.getById(agentId).subscribe({
      next: expanded => {
        this.existingAgent.set(expanded);
        this.seedEditDraft(expanded);
        this.submitting.set(false);
        this.currentStep.set(4);
      },
      error: () => {
        this.submitting.set(false);
        this.currentStep.set(4);
      },
    });
  }

  editAgain(): void {
    this.currentStep.set(2);
  }
}
