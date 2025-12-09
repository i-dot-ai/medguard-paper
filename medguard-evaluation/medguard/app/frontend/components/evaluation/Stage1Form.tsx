import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Stage1Response } from '@/types/api';
import QuestionWithReasoning from './QuestionWithReasoning';

interface Stage1FormProps {
  onSubmit: (data: Stage1Response) => Promise<void>;
  initialData?: Partial<Stage1Response>;
}

export default function Stage1Form({ onSubmit, initialData }: Stage1FormProps) {
  const router = useRouter();
  const [formData, setFormData] = useState<Stage1Response>({
    determination_possible: initialData?.determination_possible ?? null,
    determination_possible_reasoning: initialData?.determination_possible_reasoning ?? '',
  });
  
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      
      // Always save the evaluation data first
      await onSubmit(formData);
      
      // If user selected "No" for information sufficiency, redirect to homepage after saving
      if (formData.determination_possible === false) {
        router.push('/');
        return;
      }
      
    } catch (error) {
      console.error('Failed to submit evaluation:', error);
      alert('Failed to save evaluation. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isFormValid = () => {
    return formData.determination_possible !== null;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Stage 1</h3>
        <h4 className="text-lg font-semibold text-blue-900 mb-2">Information Sufficiency Check</h4>
        <p className="text-sm text-gray-700">
          Review the patient history and confirm you have sufficient information to proceed with evaluation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        <div className="flex-1 space-y-6 overflow-y-auto">
          {/* Information Sufficiency Assessment */}
          <QuestionWithReasoning
            question="Do you have sufficient information to determine if an intervention is required?"
            value={formData.determination_possible}
            onValueChange={(value) => setFormData({ ...formData, determination_possible: value as boolean | null })}
            reasoning={formData.determination_possible_reasoning || ''}
            onReasoningChange={(reasoning) => setFormData({ ...formData, determination_possible_reasoning: reasoning })}
            reasoningPlaceholder="Explain your reasoning for this assessment (optional)"
            themeColor="blue"
          />
        </div>

        {/* Submit Button */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={!isFormValid() || submitting}
            className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
          >
            {submitting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Saving...
              </div>
            ) : (
              formData.determination_possible === false ? 'Return to Homepage' : 'Proceed to Case Evaluation'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}