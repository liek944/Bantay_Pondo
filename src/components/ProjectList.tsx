import React from 'react';
import { ProjectRow, ProjectSummary } from './ProjectRow';

interface ProjectListProps {
  projects: ProjectSummary[];
  title?: string;
  subtitle?: string;
  className?: string;
}

export const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  title = 'Audited Infrastructure Projects',
  subtitle,
  className = '',
}) => {
  return (
    <div
      className={`bg-surface-container-lowest border border-hairline rounded overflow-hidden flex flex-col ${className}`}
    >
      <div className="p-space-md border-b border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm bg-surface-container-low/50">
        <div>
          <h3 className="font-headline-sm text-headline-sm font-bold text-primary">{title}</h3>
          {subtitle && (
            <p className="font-body-sm text-[0.8125rem] text-secondary mt-0.5">{subtitle}</p>
          )}
        </div>
        <span className="font-code-tabular text-body-sm text-secondary">
          {projects.length} {projects.length === 1 ? 'Project' : 'Projects'} Listed
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container border-b border-hairline font-label-caps text-label-caps uppercase text-secondary">
              <th className="py-2.5 px-4 font-bold">Contract ID</th>
              <th className="py-2.5 px-4 font-bold">Project Name &amp; Office</th>
              <th className="py-2.5 px-4 font-bold">Contractor</th>
              <th className="py-2.5 px-4 font-bold text-right">Cost (PHP)</th>
              <th className="py-2.5 px-4 font-bold">Progress</th>
              <th className="py-2.5 px-4 font-bold text-center">Audit Status</th>
              <th className="py-2.5 px-3 font-bold text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <ProjectRow key={project.contract_id} project={project} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
