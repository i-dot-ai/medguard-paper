interface QuestionWithReasoningProps {
  question: string;
  value: boolean | null | string; // Support boolean, null, or string values
  onValueChange: (value: boolean | null | string) => void;
  reasoning: string;
  onReasoningChange: (reasoning: string) => void;
  reasoningPlaceholder: string;
  themeColor: 'blue' | 'green' | 'orange' | 'purple';
  options?: Array<{ value: boolean | null | string; label: string }>; // Custom options
}

export default function QuestionWithReasoning({
  question,
  value,
  onValueChange,
  reasoning,
  onReasoningChange,
  reasoningPlaceholder,
  themeColor,
  options
}: QuestionWithReasoningProps) {
  const colorClasses = {
    blue: {
      radio: 'text-blue-600 focus:ring-blue-500',
      textField: 'focus:ring-blue-500 focus:border-blue-500'
    },
    green: {
      radio: 'text-green-600 focus:ring-green-500',
      textField: 'focus:ring-green-500 focus:border-green-500'
    },
    orange: {
      radio: 'text-orange-600 focus:ring-orange-500',
      textField: 'focus:ring-orange-500 focus:border-orange-500'
    },
    purple: {
      radio: 'text-purple-600 focus:ring-purple-500',
      textField: 'focus:ring-purple-500 focus:border-purple-500'
    }
  };

  const colors = colorClasses[themeColor];
  
  // Default options if none provided
  const defaultOptions = [
    { value: true, label: 'Yes' },
    { value: false, label: 'No' },
    { value: null, label: 'N/A' }
  ];
  
  const displayOptions = options || defaultOptions;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <h5 className="font-semibold text-gray-900 mb-3">{question}</h5>
      
      <div className="space-y-4">
        <div className="flex flex-wrap gap-4">
          {displayOptions.map((option, index) => (
            <label key={index} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                checked={value === option.value}
                onChange={() => onValueChange(option.value)}
                className={`rounded-full border-gray-300 ${colors.radio} focus:ring-2`}
              />
              <span className="font-medium text-gray-900">{option.label}</span>
            </label>
          ))}
        </div>
        
        <textarea
          value={reasoning}
          onChange={(e) => onReasoningChange(e.target.value)}
          rows={2}
          placeholder={reasoningPlaceholder}
          className={`w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 ${colors.textField} resize-none`}
        />
      </div>
    </div>
  );
}