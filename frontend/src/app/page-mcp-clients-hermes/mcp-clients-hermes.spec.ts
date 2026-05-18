import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { McpClientsHermes } from './mcp-clients-hermes';

describe('McpClientsHermes', () => {
  let component: McpClientsHermes;
  let fixture: ComponentFixture<McpClientsHermes>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [McpClientsHermes],
      providers: [provideRouter([])],
    })
    .compileComponents();

    fixture = TestBed.createComponent(McpClientsHermes);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
