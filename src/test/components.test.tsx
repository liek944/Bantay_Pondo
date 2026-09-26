import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  RiskBadge,
  MismatchScale,
  StatBlock,
  HazardBars,
  Breadcrumb,
  SearchInput,
} from '../components';
import { BrowserRouter } from 'react-router-dom';

describe('Design System Components', () => {
  it('renders RiskBadge with correct level and score', () => {
    render(<RiskBadge level="critical" score={92} />);
    expect(screen.getByText(/CRITICAL \(92\)/i)).toBeInTheDocument();
  });

  it('renders MismatchScale with four risk tiers', () => {
    render(<MismatchScale score={85} nationalPercentile={99} />);
    expect(screen.getByText(/85\/100 \(P99\)/i)).toBeInTheDocument();
    expect(screen.getByTitle('Critical Mismatch (76-100)')).toBeInTheDocument();
  });

  it('renders StatBlock with value, label, and trend', () => {
    render(
      <StatBlock
        label="Audited National Spend"
        value="₱584.2B"
        subtext="Consolidated DPWH"
        trend="+18.4% YoY"
      />
    );
    expect(screen.getByText('Audited National Spend')).toBeInTheDocument();
    expect(screen.getByText('₱584.2B')).toBeInTheDocument();
    expect(screen.getByText('+18.4% YoY')).toBeInTheDocument();
  });

  it('renders HazardBars with percentage data', () => {
    render(
      <HazardBars
        items={[
          { label: 'Flood Inundation', percentage: 84.2, riskTier: 'critical' },
          { label: 'Landslide', percentage: 12.6, riskTier: 'low' },
        ]}
      />
    );
    expect(screen.getByText('Flood Inundation')).toBeInTheDocument();
    expect(screen.getByText('84.2%')).toBeInTheDocument();
    expect(screen.getByText('Landslide')).toBeInTheDocument();
    expect(screen.getByText('12.6%')).toBeInTheDocument();
  });

  it('renders Breadcrumb with links', () => {
    render(
      <BrowserRouter>
        <Breadcrumb
          items={[
            { label: 'National Registry', path: '/' },
            { label: 'Cagayan', path: '/locality/021500000' },
            { label: 'Tuguegarao City' },
          ]}
        />
      </BrowserRouter>
    );
    expect(screen.getByText('National Registry')).toBeInTheDocument();
    expect(screen.getByText('Cagayan')).toBeInTheDocument();
    expect(screen.getByText('Tuguegarao City')).toBeInTheDocument();
  });

  it('renders SearchInput and calls onChange and onSelectChip', () => {
    const handleChange = vi.fn();
    const handleSelectChip = vi.fn();
    render(
      <SearchInput
        value="Tuguegarao"
        onChange={handleChange}
        scopeChips={['All Localities', 'Critical Anomaly']}
        activeChip="All Localities"
        onSelectChip={handleSelectChip}
      />
    );

    const input = screen.getByDisplayValue('Tuguegarao');
    expect(input).toBeInTheDocument();

    const chip = screen.getByText('Critical Anomaly');
    fireEvent.click(chip);
    expect(handleSelectChip).toHaveBeenCalledWith('Critical Anomaly');
  });
});
