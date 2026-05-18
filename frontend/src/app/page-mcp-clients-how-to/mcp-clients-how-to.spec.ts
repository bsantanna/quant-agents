import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { McpClientsHowTo } from './mcp-clients-how-to';

describe('McpClientsHowTo', () => {
  let component: McpClientsHowTo;
  let fixture: ComponentFixture<McpClientsHowTo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [McpClientsHowTo],
      providers: [provideRouter([])],
    })
    .compileComponents();

    fixture = TestBed.createComponent(McpClientsHowTo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
