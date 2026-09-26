import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';

describe('Route Rendering & Faithfulness', () => {
  it('renders Landing / National Map route (/)', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    expect(
      screen.getByText(/Where Public Billions Meet Disaster Vulnerability/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Audited National Spend/i)).toBeInTheDocument();
  });

  it('renders Locality Dashboard route (/locality/:psgcCode)', () => {
    render(
      <MemoryRouter initialEntries={['/locality/021500000']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { level: 1, name: /Tuguegarao City/i })).toBeInTheDocument();
    expect(screen.getByText(/Score 92 \/ 100/i)).toBeInTheDocument();
    expect(screen.getByText(/Audited DPWH Flood Control Projects/i)).toBeInTheDocument();
  });

  it('renders Project Detail route (/project/:contractId)', () => {
    render(
      <MemoryRouter initialEntries={['/project/22BC0045']}>
        <App />
      </MemoryRouter>
    );
    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /Construction of River Dike along Cagayan River Phase III/i,
      })
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Negative Slippage/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Auditor-General & Watchdog Red Flags/i)).toBeInTheDocument();
  });

  it('renders Contractor Profile route (/contractor/:id)', () => {
    render(
      <MemoryRouter initialEntries={['/contractor/alpha-omega']}>
        <App />
      </MemoryRouter>
    );
    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /Alpha & Omega Gen\. Contractor & Devt\. Corp\./i,
      })
    ).toBeInTheDocument();
    expect(screen.getByText(/Total Awarded Spend/i)).toBeInTheDocument();
    expect(screen.getByText(/Congressional District Concentration/i)).toBeInTheDocument();
  });

  it('renders Compare View route (/compare)', () => {
    render(
      <MemoryRouter initialEntries={['/compare?a=021500000&b=035413000']}>
        <App />
      </MemoryRouter>
    );
    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /Side-by-Side Expenditure vs\. Vulnerability/i,
      })
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Locality A/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Locality B/i).length).toBeGreaterThan(0);
  });

  it('renders Methodology / Whistleblower route (/methodology)', () => {
    render(
      <MemoryRouter initialEntries={['/methodology']}>
        <App />
      </MemoryRouter>
    );
    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /Whistleblower Vault & Methodology/i,
      })
    ).toBeInTheDocument();
    expect(screen.getByText(/Forensic Intake Form/i)).toBeInTheDocument();
  });
});
