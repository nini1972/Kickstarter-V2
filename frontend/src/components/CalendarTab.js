import React, { useState, useEffect } from 'react';
import { useProjects } from '../hooks/useQuery';
import { useAppContext } from '../context/AppContext';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const CalendarTab = () => {
  const { data: projects, isLoading, error } = useProjects();
  const { setActiveTab } = useAppContext();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [calendarDays, setCalendarDays] = useState([]);
  const [projectsByDay, setProjectsByDay] = useState({});

  // Generate calendar days for the current month
  useEffect(() => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    
    // First day of the month
    const firstDay = new Date(year, month, 1);
    // Last day of the month
    const lastDay = new Date(year, month + 1, 0);
    
    // Get the day of the week for the first day (0 = Sunday, 6 = Saturday)
    const firstDayOfWeek = firstDay.getDay();
    
    // Calculate days from previous month to show
    const daysFromPrevMonth = firstDayOfWeek;
    
    // Calculate total days to show (previous month days + current month days)
    const totalDays = daysFromPrevMonth + lastDay.getDate();
    
    // Calculate rows needed (7 days per row)
    const rows = Math.ceil(totalDays / 7);
    
    // Calculate total calendar days (rows * 7)
    const calendarDaysCount = rows * 7;
    
    // Generate calendar days
    const days = [];
    let currentDate = new Date(firstDay);
    currentDate.setDate(currentDate.getDate() - daysFromPrevMonth);
    
    for (let i = 0; i < calendarDaysCount; i++) {
      days.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    setCalendarDays(days);
  }, [selectedDate]);

  // Group projects by day
  useEffect(() => {
    if (projects) {
      const byDay = {};
      
      projects.forEach(project => {
        const deadline = new Date(project.deadline);
        const dateKey = deadline.toISOString().split('T')[0];
        
        if (!byDay[dateKey]) {
          byDay[dateKey] = [];
        }
        
        byDay[dateKey].push(project);
      });
      
      setProjectsByDay(byDay);
    }
  }, [projects]);

  const handlePrevMonth = () => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() - 1);
    setSelectedDate(newDate);
  };

  const handleNextMonth = () => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + 1);
    setSelectedDate(newDate);
  };

  const isToday = (date) => {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  };

  const isCurrentMonth = (date) => {
    return date.getMonth() === selectedDate.getMonth();
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        Error loading calendar data: {error.message}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">
          {selectedDate.getFullYear()} {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][selectedDate.getMonth()]}
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={handlePrevMonth}
            className="p-2 rounded-full hover:bg-gray-100"
          >
            &lt;
          </button>
          <button
            onClick={handleNextMonth}
            className="p-2 rounded-full hover:bg-gray-100"
          >
            &gt;
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-7 gap-px bg-gray-200">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, i) => (
          <div key={i} className="bg-gray-50 py-2 text-center text-sm font-semibold text-gray-700">
            {day}
          </div>
        ))}
        
        {calendarDays.map((date, i) => {
          const dateKey = date.toISOString().split('T')[0];
          const dayProjects = projectsByDay[dateKey] || [];
          
          return (
            <div
              key={i}
              className={`bg-white p-2 h-32 overflow-y-auto ${
                isToday(date) ? 'bg-blue-50' : ''
              } ${
                !isCurrentMonth(date) ? 'text-gray-400' : ''
              }`}
            >
              <div className="font-semibold text-sm mb-1">{date.getDate()}</div>
              
              {dayProjects.map((project, j) => (
                <div
                  key={j}
                  className="p-1 mb-1 text-xs rounded bg-gray-100 hover:bg-gray-200 cursor-pointer"
                  onClick={() => setActiveTab('projects')}
                >
                  <div className="font-medium truncate">{project.name}</div>
                  
                  <div className="flex justify-between items-center mt-1">
                    <div className="flex items-center">
                      {project.risk_level === 'low' && (
                        <CheckCircleIcon className="h-3 w-3 text-green-500 mr-1" />
                      )}
                      {project.risk_level === 'medium' && (
                        <ClockIcon className="h-3 w-3 text-yellow-500 mr-1" />
                      )}
                      {project.risk_level === 'high' && (
                        <ExclamationTriangleIcon className="h-3 w-3 text-red-500 mr-1" />
                      )}
                      <span className="text-xs">{project.risk_level}</span>
                    </div>
                    
                    <div className="text-right ml-6">
                      <div className="flex flex-col items-end">
                        <div className="text-sm font-medium text-gray-900">
                          {project.deadline ? new Date(project.deadline).toDateString() : 'No deadline'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {project.deadline ? new Date(project.deadline).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : ''}
                        </div>
                        <div className="text-xs text-gray-500">
                          <span className="font-medium">Launched:</span> {project.launched_date ? new Date(project.launched_date).toDateString() : 'Unknown'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CalendarTab;