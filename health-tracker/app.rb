require "sinatra"
require "date"
require_relative "lib/meal_repository"
require_relative "lib/weight_repository"
require_relative "lib/report_generator"

configure do
  set :views, File.join(__dir__, "views")
  set :public_folder, File.join(__dir__, "public")
  set :bind, "0.0.0.0"
end

meal_repo = MealRepository.new
weight_repo = WeightRepository.new
report_generator = ReportGenerator.new(meal_repo: meal_repo, weight_repo: weight_repo)

helpers do
  def today
    Date.today
  end

  def parse_date(param)
    param && !param.empty? ? Date.parse(param) : today
  end

  def format_num(value)
    return "-" if value.nil?

    value.to_f.round(1)
  end
end

get "/" do
  @date = today
  @meals = meal_repo.for_date(@date)
  @weights = weight_repo.for_date(@date)
  @totals = meal_repo.daily_totals(@date)
  erb :index
end

get "/meals/new" do
  @meal_type = params[:meal_type] || "breakfast"
  erb :meal_new
end

post "/meals" do
  meal_type = params[:meal_type]
  halt 400, "meal_type is required" unless MealRepository::MEAL_TYPES.include?(meal_type)

  photo = params[:photo]
  text = params[:text]

  begin
    if photo && photo[:tempfile]
      record = meal_repo.record(
        date: today,
        meal_type: meal_type,
        text: text,
        image_bytes: photo[:tempfile].read,
        media_type: photo[:type] || "image/jpeg",
        input_type: "photo"
      )
    elsif text && !text.strip.empty?
      record = meal_repo.record(date: today, meal_type: meal_type, text: text, input_type: "text")
    else
      halt 400, "photo or text is required"
    end
  rescue StandardError => e
    @error = "食事の分析に失敗しました: #{e.message}"
    @meal_type = meal_type
    halt 500, erb(:meal_new)
  end

  @record = record
  erb :meal_created
end

get "/weights/new" do
  @time_of_day = params[:time_of_day] || "morning"
  erb :weight_new
end

post "/weights" do
  time_of_day = params[:time_of_day]
  halt 400, "time_of_day is required" unless WeightRepository::TIMES_OF_DAY.include?(time_of_day)
  halt 400, "weight_kg is required" if params[:weight_kg].to_s.strip.empty?

  weight_repo.record(date: today, time_of_day: time_of_day, weight_kg: params[:weight_kg], note: params[:note])
  redirect "/"
end

get "/report" do
  @date = parse_date(params[:date])
  begin
    @result = report_generator.generate(@date)
  rescue StandardError => e
    @error = "レポート生成に失敗しました: #{e.message}"
  end
  erb :report
end

get "/history" do
  @end_date = today
  @start_date = @end_date - 6
  @meal_history = meal_repo.history(@start_date, @end_date)
  @weight_history = weight_repo.history(@start_date, @end_date)
  erb :history
end
