import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ChevronRight } from 'lucide-react';

export interface ProjectSummary {
  contract_id: string;
  title: string;
  contractor_name?: string;
  contractor_id?: string;
  implementing_office?: string;
  budget_php: number;
  contract_cost_php?: number;
  physical_progress_pct: number;
  target_completion_date?: string;
  flags_count?: number;
  is_delayed?: boolean;
}

interface ProjectRowProps {
  project: ProjectSummary;
}

export const ProjectRow: React.FC<ProjectRowProps> = ({ project }) => {
  const formatPeso = (val: number) => {
    if (val >= 1e9) return `₱${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `₱${(val / 1e6).toFixed(1)}M`;
    return `₱${val.toLocaleString()}`;
  };

  return (
    <tr className="border-b border-hairline hover:bg-surface-container-low transition-colors group">
      {/* Contract ID */}
      <td className="py-3 px-4 font-code-tabular text-code-tabular font-medium text-primary">
        <Link
          to={`/project/${project.contract_id}`}
          className="hover:underline flex items-center gap-1"
        >
          {project.contract_id}
        </Link>
      </td>

      {/* Project Title & Office */}
      <td className="py-3 px-4 max-w-md">
        <Link to={`/project/${project.contract_id}`} className="block">
          <span className="font-body-sm font-semibold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">
            {project.title}
          </span>
          {project.implementing_office && (
            <span className="font-label-caps text-[0.625rem] text-secondary uppercase block mt-0.5">
              {project.implementing_office}
            </span>
          )}
        </Link>
      </td>

      {/* Contractor */}
      <td className="py-3 px-4 font-body-sm text-body-sm text-on-surface-variant">
        {project.contractor_id ? (
          <Link
            to={`/contractor/${project.contractor_id}`}
            className="hover:text-primary hover:underline"
          >
            {project.contractor_name || 'Unspecified Contractor'}
          </Link>
        ) : (
          <span>{project.contractor_name || 'Direct Administration'}</span>
        )}
      </td>

      {/* Allocation / Cost */}
      <td className="py-3 px-4 font-code-tabular text-code-tabular font-bold text-on-surface text-right whitespace-nowrap">
        {formatPeso(project.contract_cost_php || project.budget_php)}
      </td>

      {/* Progress */}
      <td className="py-3 px-4 whitespace-nowrap min-w-[140px]">
        <div className="flex items-center gap-2">
          <div className="w-full bg-surface-container h-2 rounded overflow-hidden">
            <div
              className={`h-full rounded ${
                project.physical_progress_pct >= 100
                  ? 'bg-accent'
                  : project.is_delayed
                    ? 'bg-risk-500'
                    : 'bg-primary'
              }`}
              style={{ width: `${Math.min(100, project.physical_progress_pct)}%` }}
            />
          </div>
          <span className="font-code-tabular text-[0.75rem] font-medium text-secondary w-10 text-right">
            {project.physical_progress_pct.toFixed(0)}%
          </span>
        </div>
      </td>

      {/* Flags / Audit status */}
      <td className="py-3 px-4 text-center whitespace-nowrap">
        {project.flags_count && project.flags_count > 0 ? (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-risk-high-bg border border-risk-high-border text-risk-high-text font-label-caps text-[0.6875rem] font-bold">
            <AlertTriangle className="w-3 h-3 text-risk-500" />
            {project.flags_count} {project.flags_count === 1 ? 'FLAG' : 'FLAGS'}
          </span>
        ) : (
          <span className="text-secondary font-label-caps text-[0.625rem] uppercase">Clear</span>
        )}
      </td>

      {/* Action */}
      <td className="py-3 px-3 text-right">
        <Link
          to={`/project/${project.contract_id}`}
          className="p-1 rounded text-secondary hover:text-primary transition-colors inline-block"
          aria-label={`View ${project.contract_id}`}
        >
          <ChevronRight className="w-4 h-4" />
        </Link>
      </td>
    </tr>
  );
};
