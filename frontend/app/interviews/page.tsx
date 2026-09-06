'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Shell, Top } from '../../components/Shell';
import { api } from '../../lib/api';

export default function Interviews() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api<any[]>('/interviews').then(setItems);
  }, []);

  return (
    <Shell>
      <Top
        title="Interviews"
        action={
          <Link
            href="/interviews/new"
            className="btn btn-primary flex gap-2 items-center"
          >
            <Plus size={16} /> Create interview
          </Link>
        }
      />

      <div className="p-6 md:p-9">
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left bg-gray-50 text-gray-500">
                <th className="p-4">Candidate</th>
                <th>Position</th>
                <th>Status</th>
                <th>Score</th>
                <th>Recommendation</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {items.map((i) => (
                <tr className="border-t" key={i.id}>
                  <td className="p-4 font-semibold">
                    {i.candidate_name || 'Awaiting candidate'}
                  </td>
                  <td>{i.job_title}</td>
                  <td>{i.status.replaceAll('_', ' ')}</td>
                  <td>{i.overall_score ?? '—'}</td>
                  <td>
                    {i.recommendation?.replace('_', ' ') || '—'}
                  </td>
                  <td>
                    <Link
                      className="font-semibold text-blue-600"
                      href={`/interviews/${i.id}`}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}
