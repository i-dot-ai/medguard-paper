import { useState, useEffect, useRef } from 'react';
import { EventType, EventFilters } from '@/types/api';

interface EventFiltersProps {
  filters: EventFilters;
  onFiltersChange: (filters: EventFilters) => void;
  smrDate?: string | null;
}

export default function EventFiltersComponent({ filters, onFiltersChange, smrDate }: EventFiltersProps) {
  const [showEventTypeDropdown, setShowEventTypeDropdown] = useState(false);
  const [showQuickDateSelect, setShowQuickDateSelect] = useState(false);
  const [monthsBefore, setMonthsBefore] = useState(6);
  const [monthsAfter, setMonthsAfter] = useState(6);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const quickDateRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowEventTypeDropdown(false);
      }
      if (quickDateRef.current && !quickDateRef.current.contains(event.target as Node)) {
        setShowQuickDateSelect(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Convert date to UK format for display (dd/mm/yyyy)
  const formatDateForDisplay = (dateString: string | undefined): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  // Convert UK format date input (dd/mm/yyyy) to ISO format (yyyy-mm-dd)
  const parseUKDateToISO = (ukDate: string): string => {
    const parts = ukDate.split('/');
    if (parts.length === 3) {
      const [day, month, year] = parts;
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    return ukDate; // Return as is if not in expected format
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ ...filters, searchTerm: e.target.value });
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ 
      ...filters, 
      dateFrom: e.target.value || undefined 
    });
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ 
      ...filters, 
      dateTo: e.target.value || undefined 
    });
  };

  // Apply quick date selection relative to SMR date
  const applyQuickDateSelection = (beforeMonths: number, afterMonths: number) => {
    if (!smrDate) return;
    
    const smr = new Date(smrDate);
    const fromDate = new Date(smr);
    const toDate = new Date(smr);
    
    fromDate.setMonth(fromDate.getMonth() - beforeMonths);
    toDate.setMonth(toDate.getMonth() + afterMonths);
    
    onFiltersChange({
      ...filters,
      dateFrom: fromDate.toISOString().split('T')[0],
      dateTo: toDate.toISOString().split('T')[0]
    });
    
    setShowQuickDateSelect(false);
  };

  const handleEventTypeChange = (eventType: EventType, checked: boolean) => {
    const newEventTypes = checked
      ? [...filters.eventTypes, eventType]
      : filters.eventTypes.filter(type => type !== eventType);
    
    onFiltersChange({ ...filters, eventTypes: newEventTypes });
  };

  const clearFilters = () => {
    onFiltersChange({
      searchTerm: '',
      dateFrom: undefined,
      dateTo: undefined,
      eventTypes: []
    });
  };

  const formatEventType = (type: string) => {
    return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-gray-50 rounded border mb-4">
      {/* Search - inline */}
      <input
        type="text"
        value={filters.searchTerm}
        onChange={handleSearchChange}
        placeholder="Search events..."
        className="flex-1 min-w-[200px] px-3 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
      />

      {/* Date Range - inline with UK format placeholders */}
      <input
        type="date"
        value={filters.dateFrom || ''}
        onChange={handleDateFromChange}
        className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        title="From date (dd/mm/yyyy)"
        placeholder="dd/mm/yyyy"
      />
      <span className="text-gray-400 text-sm">to</span>
      <input
        type="date"
        value={filters.dateTo || ''}
        onChange={handleDateToChange}
        className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        title="To date (dd/mm/yyyy)"
        placeholder="dd/mm/yyyy"
      />

      {/* Quick Date Selection - only show if SMR date is available */}
      {smrDate && (
        <div className="relative" ref={quickDateRef}>
          <button
            type="button"
            onClick={() => setShowQuickDateSelect(!showQuickDateSelect)}
            className="px-3 py-1 border border-gray-300 rounded text-sm bg-white hover:bg-gray-50 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 flex items-center gap-2"
          >
            <span>Quick Select</span>
            <svg className={`w-4 h-4 transition-transform ${showQuickDateSelect ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showQuickDateSelect && (
            <div className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded shadow-lg z-10">
              <div className="p-3 space-y-3">
                <div className="text-xs font-semibold text-gray-700 mb-2">
                  Select period around SMR date ({new Date(smrDate).toLocaleDateString('en-GB')})
                </div>
                
                {/* Months Before SMR */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600 w-24">Months before:</label>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    value={monthsBefore}
                    onChange={(e) => setMonthsBefore(parseInt(e.target.value) || 0)}
                    className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
                
                {/* Months After SMR */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600 w-24">Months after:</label>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    value={monthsAfter}
                    onChange={(e) => setMonthsAfter(parseInt(e.target.value) || 0)}
                    className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
                
                {/* Apply Button */}
                <button
                  onClick={() => applyQuickDateSelection(monthsBefore, monthsAfter)}
                  className="w-full px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
                >
                  Apply Date Range
                </button>
                
                {/* Quick Presets */}
                <div className="border-t pt-2 mt-2">
                  <div className="text-xs text-gray-600 mb-1">Quick presets:</div>
                  <div className="space-y-1">
                    <button
                      onClick={() => applyQuickDateSelection(6, 6)}
                      className="w-full text-left px-2 py-1 text-xs hover:bg-gray-100 rounded"
                    >
                      6 months before & after SMR
                    </button>
                    <button
                      onClick={() => applyQuickDateSelection(3, 3)}
                      className="w-full text-left px-2 py-1 text-xs hover:bg-gray-100 rounded"
                    >
                      3 months before & after SMR
                    </button>
                    <button
                      onClick={() => applyQuickDateSelection(12, 0)}
                      className="w-full text-left px-2 py-1 text-xs hover:bg-gray-100 rounded"
                    >
                      12 months before SMR only
                    </button>
                    <button
                      onClick={() => applyQuickDateSelection(0, 12)}
                      className="w-full text-left px-2 py-1 text-xs hover:bg-gray-100 rounded"
                    >
                      12 months after SMR only
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Event Types Dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setShowEventTypeDropdown(!showEventTypeDropdown)}
          className="px-3 py-1 border border-gray-300 rounded text-sm bg-white hover:bg-gray-50 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 flex items-center gap-2"
        >
          <span>
            {filters.eventTypes.length === 0 
              ? 'Event Types' 
              : `${filters.eventTypes.length} selected`}
          </span>
          <svg className={`w-4 h-4 transition-transform ${showEventTypeDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {showEventTypeDropdown && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded shadow-lg z-10">
            <div className="p-2 max-h-64 overflow-y-auto">
              {Object.values(EventType).map((eventType) => (
                <label key={eventType} className="flex items-center p-2 hover:bg-gray-50 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.eventTypes.includes(eventType)}
                    onChange={(e) => handleEventTypeChange(eventType, e.target.checked)}
                    className="mr-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{formatEventType(eventType)}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Clear Filters */}
      {(filters.searchTerm || filters.dateFrom || filters.dateTo || filters.eventTypes.length > 0) && (
        <button
          onClick={clearFilters}
          className="text-sm text-blue-600 hover:text-blue-800 underline"
        >
          Clear
        </button>
      )}
    </div>
  );
}